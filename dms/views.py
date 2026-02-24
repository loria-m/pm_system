from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from .models import User, Document, Department, DocumentRouting, DocumentLog, Notification
from .forms import (
    UserRegistrationForm, LoginForm, DocumentCreateForm,
    DocumentClassifyForm, DocumentAssignForm, DocumentReviewForm,
    DocumentRoutingForm, UserRoleForm, DocumentSearchForm
)
from .decorators import role_required
from .utils import notify_user, log_action


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'dept_sender_receiver'
        user.save()
        messages.success(request, 'Account registered! Please wait for role assignment.')
        return redirect('login')
    return render(request, 'auth/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    docs = Document.objects.all()
    if user.role == 'dept_sender_receiver':
        docs = docs.filter(Q(created_by=user) | Q(assigned_to=user))
    elif user.role in ('dept_head', 'governor', 'executive'):
        if user.department:
            docs = docs.filter(Q(current_department=user.department) | Q(origin_department=user.department))
    unread_notifications = request.user.notifications.filter(is_read=False).count()
    ctx = {
        'total': docs.count(),
        'pending': docs.filter(status='pending_review').count(),
        'approved': docs.filter(status='approved').count(),
        'archived': docs.filter(status='archived').count(),
        'recent_docs': docs.order_by('-updated_at')[:5],
        'unread_notifications': unread_notifications,
    }
    return render(request, 'dashboard.html', ctx)


# ─── DOCUMENT VIEWS ───────────────────────────────────────────────────────────

@login_required
def document_list(request):
    form = DocumentSearchForm(request.GET or None)
    docs = Document.objects.all().order_by('-created_at')
    user = request.user

    if user.role == 'dept_sender_receiver':
        docs = docs.filter(Q(created_by=user) | Q(assigned_to=user))
    elif user.role in ('dept_head',):
        if user.department:
            docs = docs.filter(Q(current_department=user.department) | Q(origin_department=user.department))

    if form.is_valid():
        q = form.cleaned_data.get('query')
        status = form.cleaned_data.get('status')
        source = form.cleaned_data.get('source')
        if q:
            docs = docs.filter(Q(title__icontains=q) | Q(reference_number__icontains=q))
        if status:
            docs = docs.filter(status=status)
        if source:
            docs = docs.filter(source=source)

    return render(request, 'documents/list.html', {'docs': docs, 'form': form})


@login_required
def document_create(request):
    form = DocumentCreateForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.created_by = request.user
        doc.origin_department = request.user.department
        doc.current_department = request.user.department

        if doc.source == 'internal':
            doc.status = 'draft'
        else:
            doc.status = 'pending_review'
            doc.logged_at = timezone.now()

        doc.save()
        log_action(doc, request.user, 'created')

        if doc.source == 'external':
            log_action(doc, request.user, 'logged')
            # Notify dept head
            dept_heads = User.objects.filter(role='dept_head', department=request.user.department)
            for dh in dept_heads:
                notify_user(dh, doc, f"New external document received: {doc.reference_number}")

        messages.success(request, f'Document {doc.reference_number} created successfully.')
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/create.html', {'form': form})


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    logs = doc.logs.all()
    routings = doc.routings.all()
    return render(request, 'documents/detail.html', {'doc': doc, 'logs': logs, 'routings': routings})


@login_required
@role_required(['super_admin', 'dept_head'])
def document_classify(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    form = DocumentClassifyForm(request.POST or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_action(doc, request.user, 'classified')
        # Notify dept head to assign
        dept_heads = User.objects.filter(role='dept_head', department=doc.current_department)
        for dh in dept_heads:
            notify_user(dh, doc, f"Document classified, please assign: {doc.reference_number}")
        messages.success(request, 'Document classified.')
        return redirect('document_assign', pk=doc.pk)
    return render(request, 'documents/classify.html', {'form': form, 'doc': doc})


@login_required
@role_required(['super_admin', 'dept_head'])
def document_assign(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    form = DocumentAssignForm(request.POST or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.status = 'pending_review'
        doc.save()
        log_action(doc, request.user, 'assigned')
        notify_user(doc.assigned_to, doc, f"You have been assigned document: {doc.reference_number}")
        messages.success(request, 'Document assigned to action officer.')
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/assign.html', {'form': form, 'doc': doc})


@login_required
def document_process(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        doc.description = doc.description + f"\n[Processed by {request.user}]: {notes}"
        doc.status = 'pending_review'
        doc.save()
        log_action(doc, request.user, 'processed', notes)
        # Notify dept head to review
        dept_heads = User.objects.filter(role='dept_head', department=doc.current_department)
        for dh in dept_heads:
            notify_user(dh, doc, f"Document processed and ready for review: {doc.reference_number}")
        messages.success(request, 'Document processed. Sent for review.')
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/process.html', {'doc': doc})


@login_required
@role_required(['dept_head', 'governor', 'executive', 'super_admin'])
def document_review(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    form = DocumentReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        decision = form.cleaned_data['decision']
        notes = form.cleaned_data.get('notes', '')
        if decision == 'approve':
            doc.status = 'approved'
            log_action(doc, request.user, 'approved', notes)
            messages.success(request, 'Document approved.')
            return redirect('document_esign', pk=doc.pk)
        else:
            doc.status = 'return_for_revision'
            doc.save()
            log_action(doc, request.user, 'revision', notes)
            if doc.assigned_to:
                notify_user(doc.assigned_to, doc, f"Document returned for revision: {doc.reference_number}")
            messages.warning(request, 'Document returned for revision.')
            return redirect('document_detail', pk=doc.pk)
        doc.save()
    return render(request, 'documents/review.html', {'form': form, 'doc': doc})


@login_required
@role_required(['dept_head', 'governor', 'executive', 'super_admin'])
def document_esign(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        if 'esignature' in request.FILES:
            doc.esignature = request.FILES['esignature']
        doc.status = 'esigned'
        doc.save()
        log_action(doc, request.user, 'esigned')
        messages.success(request, 'Document e-signed.')
        return redirect('document_route_decision', pk=doc.pk)
    return render(request, 'documents/esign.html', {'doc': doc})


@login_required
@role_required(['dept_head', 'governor', 'executive', 'super_admin'])
def document_route_decision(request, pk):
    """Decide: route to another office or finalize"""
    doc = get_object_or_404(Document, pk=pk)
    departments = Department.objects.exclude(pk=doc.current_department.pk if doc.current_department else None)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'route':
            to_dept_id = request.POST.get('to_department')
            to_dept = get_object_or_404(Department, pk=to_dept_id)
            notes = request.POST.get('notes', '')
            DocumentRouting.objects.create(
                document=doc,
                from_department=doc.current_department,
                to_department=to_dept,
                forwarded_by=request.user,
                notes=notes,
            )
            doc.current_department = to_dept
            doc.status = 'pending_review'
            doc.save()
            log_action(doc, request.user, 'routed', f"Routed to {to_dept}")
            dept_heads = User.objects.filter(role='dept_head', department=to_dept)
            for dh in dept_heads:
                notify_user(dh, doc, f"Document routed to your office: {doc.reference_number}")
            messages.success(request, f'Document routed to {to_dept}.')
        elif action == 'release_correspondent':
            doc.status = 'released'
            doc.save()
            log_action(doc, request.user, 'released')
            messages.success(request, 'Document released to correspondent.')
            return redirect('document_notify', pk=doc.pk)
        elif action == 'return_origin':
            doc.status = 'returned'
            doc.action_type = 'return'
            doc.save()
            log_action(doc, request.user, 'returned')
            if doc.origin_department:
                origin_staff = User.objects.filter(department=doc.origin_department)
                for u in origin_staff:
                    notify_user(u, doc, f"Document returned to your office: {doc.reference_number}")
            messages.success(request, 'Document returned to origin.')
            return redirect('document_notify', pk=doc.pk)
        elif action == 'release_agency':
            doc.status = 'released'
            doc.action_type = 'release'
            doc.save()
            log_action(doc, request.user, 'released')
            messages.success(request, 'Document released to external agency.')
            return redirect('document_notify', pk=doc.pk)
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/route_decision.html', {'doc': doc, 'departments': departments})


@login_required
def document_notify(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        log_action(doc, request.user, 'notified', notes)
        # Auto-archive after notify
        doc.status = 'archived'
        doc.save()
        log_action(doc, request.user, 'archived')
        messages.success(request, 'Parties notified and document archived.')
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/notify.html', {'doc': doc})


# ─── ADMIN VIEWS ──────────────────────────────────────────────────────────────

@login_required
@role_required(['super_admin'])
def manage_users(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'admin/users.html', {'users': users})


@login_required
@role_required(['super_admin'])
def assign_role(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserRoleForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Role updated for {user.username}.')
        return redirect('manage_users')
    return render(request, 'admin/assign_role.html', {'form': form, 'target_user': user})


@login_required
@role_required(['super_admin'])
def manage_departments(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        if name and code:
            Department.objects.create(name=name, code=code)
            messages.success(request, 'Department created.')
    return render(request, 'admin/departments.html', {'departments': departments})


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifs': notifs})


@login_required
def notifications_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})
