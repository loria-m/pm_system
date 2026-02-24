# Paperless Management System (PMS)
## Django Web Application — Complete Setup Guide

---

## 📋 Project Overview

This Django webapp implements a **Paperless Document Management System** based on:
- **Flowchart**: Document lifecycle (create → review → approve → e-sign → route → archive)
- **Use Case Diagram**: 5 actor roles with specific permissions

### Actor Roles & Permissions

| Role | Key Permissions |
|------|----------------|
| **Super Admin** | Full access, user/department management, all document actions |
| **Dept. Sender/Receiver** | Create documents, process assigned documents, send/receive |
| **Dept. Head** | Review, approve/reject, classify, assign, e-sign, route |
| **Governor** | Review, approve, e-sign documents |
| **Executive** | Review documents, approve/reject |

---

## 🗂 Project Structure

```
paperless_pms/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── dms/                          ← Main app
    ├── __init__.py
    ├── apps.py
    ├── models.py                 ← Database models
    ├── views.py                  ← Business logic
    ├── forms.py                  ← Django forms
    ├── urls.py                   ← URL routing
    ├── admin.py                  ← Django admin config
    ├── decorators.py             ← Role-based access decorators
    ├── utils.py                  ← Helper functions
    └── templates/
        ├── base.html             ← Main layout with sidebar
        ├── dashboard.html
        ├── notifications.html
        ├── auth/
        │   ├── login.html
        │   └── register.html
        ├── documents/
        │   ├── list.html
        │   ├── create.html
        │   ├── detail.html
        │   ├── classify.html
        │   ├── assign.html
        │   ├── process.html
        │   ├── review.html
        │   ├── esign.html
        │   ├── route_decision.html
        │   └── notify.html
        └── admin/
            ├── users.html
            ├── assign_role.html
            └── departments.html
```

---

## ⚙️ Step-by-Step Installation

### Step 1: Prerequisites

Make sure you have the following installed:
- **Python 3.10+** → `python --version`
- **pip** → `pip --version`
- **git** (optional)

### Step 2: Create Project Directory & Virtual Environment

```bash
# Create project folder
mkdir paperless_pms
cd paperless_pms

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install Django==4.2 Pillow gunicorn whitenoise
```

Or using requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 4: Create the Django Project & App

```bash
# Create Django project
django-admin startproject config .

# Create the dms app
python manage.py startapp dms
```

### Step 5: Copy All Code Files

Copy all the provided files into the correct locations:

```
config/settings.py   ← Replace generated settings.py
config/urls.py       ← Replace generated urls.py
dms/models.py        ← Replace generated models.py
dms/views.py         ← Replace generated views.py
dms/forms.py         ← Create new file
dms/urls.py          ← Create new file
dms/admin.py         ← Replace generated admin.py
dms/apps.py          ← Replace generated apps.py
dms/decorators.py    ← Create new file
dms/utils.py         ← Create new file
dms/templates/       ← Create templates folder with all HTML files
```

### Step 6: Configure settings.py

Make sure these key settings are correct:

```python
# settings.py

INSTALLED_APPS = [
    ...
    'dms',  # Add this line
]

AUTH_USER_MODEL = 'dms.User'   # Custom user model

TEMPLATES = [{
    ...
    'DIRS': [BASE_DIR / 'dms' / 'templates'],  # Template directory
    ...
}]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Step 7: Create and Apply Database Migrations

```bash
# Create migration files from models
python manage.py makemigrations dms

# Apply migrations to create database tables
python manage.py migrate
```

Expected output:
```
Applying dms.0001_initial... OK
```

### Step 8: Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Enter:
- **Username**: `admin`
- **Email**: `admin@example.com`
- **Password**: `Admin@123` (or your preferred password)

### Step 9: Create Static & Media Directories

```bash
mkdir -p static media
```

### Step 10: Run the Development Server

```bash
python manage.py runserver
```

Open browser and navigate to: **http://127.0.0.1:8000**

---

## 🚀 Initial Setup After Running

### Create Departments (as Super Admin)

1. Log in at http://127.0.0.1:8000/login/ with your superuser credentials
2. Go to **Administration → Departments**
3. Add your departments, e.g.:
   - Name: `Governor's Office`, Code: `GOV`
   - Name: `Finance Department`, Code: `FIN`
   - Name: `Records Office`, Code: `REC`

### Create Test Users

1. Go to **Administration → Manage Users**
2. New users can register at http://127.0.0.1:8000/register/
3. As Super Admin, click **Edit Role** to assign roles and departments

### Test the Document Workflow

#### Internal Document Flow:
1. Login as **Dept. Sender/Receiver**
2. Click **New Document** → Source: Internal → Fill form → Create
3. Login as **Dept. Head** → find document → **Review & Approve**
4. Dept. Head → **E-Sign Document**
5. Dept. Head → **Route / Release** (route to next dept or release)
6. Final step → **Notify & Archive**

#### External Document Flow:
1. Login as **Dept. Sender/Receiver**
2. Click **New Document** → Source: External → Fill correspondent info
3. Login as **Dept. Head** → **Classify** → **Assign Officer**
4. Assigned officer → **Process Document**
5. Dept. Head → **Review & Approve**
6. Dept. Head → **E-Sign**
7. Dept. Head → **Route / Release**

---

## 🗃 Database Models

### User
Extends Django's AbstractUser with:
- `role`: super_admin, dept_sender_receiver, dept_head, governor, executive
- `department`: ForeignKey to Department

### Document
Main document model with:
- `title`, `reference_number` (auto-generated: DOC-2024-00001)
- `source`: internal or external
- `status`: draft → pending_review → approved → esigned → released/returned → archived
- `classification`: confidential, internal, public
- `file`: uploaded document attachment
- `esignature`: uploaded signature image
- Links to creator, assignee, origin and current department

### DocumentRouting
Tracks document movement between departments:
- `from_department`, `to_department`
- `forwarded_by`, `forwarded_at`
- `notes`

### DocumentLog
Audit trail of all actions:
- `action`: created, logged, classified, assigned, processed, reviewed, approved, etc.
- `user`, `timestamp`, `notes`

### Notification
In-app notifications:
- `recipient`, `message`, `is_read`
- `document` (optional link)

---

## 🔗 URL Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | index | Redirects to login/dashboard |
| `/login/` | login_view | Login page |
| `/logout/` | logout_view | Logout |
| `/register/` | register_view | User registration |
| `/dashboard/` | dashboard | Main dashboard |
| `/documents/` | document_list | All documents with search |
| `/documents/create/` | document_create | Create new document |
| `/documents/<id>/` | document_detail | View document + actions |
| `/documents/<id>/classify/` | document_classify | Set classification |
| `/documents/<id>/assign/` | document_assign | Assign action officer |
| `/documents/<id>/process/` | document_process | Process document |
| `/documents/<id>/review/` | document_review | Approve/reject |
| `/documents/<id>/esign/` | document_esign | Electronic signature |
| `/documents/<id>/route/` | document_route_decision | Route or release |
| `/documents/<id>/notify/` | document_notify | Notify & archive |
| `/admin-panel/users/` | manage_users | List all users |
| `/admin-panel/users/<id>/role/` | assign_role | Edit user role |
| `/admin-panel/departments/` | manage_departments | Manage departments |
| `/notifications/` | notifications_view | View notifications |
| `/admin/` | Django Admin | Built-in admin panel |

---

## 🛡 Role-Based Access Control

The `@role_required(['role1', 'role2'])` decorator protects views:

```python
@login_required
@role_required(['dept_head', 'super_admin'])
def document_classify(request, pk):
    ...
```

Role access matrix:

| Action | Super Admin | Dept. Head | Sender/Receiver | Governor | Executive |
|--------|:-----------:|:----------:|:---------------:|:--------:|:---------:|
| Create Document | ✅ | ✅ | ✅ | ✅ | ✅ |
| Assign Role | ✅ | ❌ | ❌ | ❌ | ❌ |
| Classify Document | ✅ | ✅ | ❌ | ❌ | ❌ |
| Assign Officer | ✅ | ✅ | ❌ | ❌ | ❌ |
| Process Document | ✅ | ✅ | ✅ | ❌ | ❌ |
| Review/Approve | ✅ | ✅ | ❌ | ✅ | ✅ |
| E-Sign | ✅ | ✅ | ❌ | ✅ | ✅ |
| Route Document | ✅ | ✅ | ❌ | ✅ | ✅ |

---

## 🔧 Production Deployment

### Using Gunicorn + Nginx

```bash
# Install production dependencies
pip install gunicorn whitenoise

# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Key settings.py changes for production:

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.environ.get('SECRET_KEY')  # Use environment variable

# Add WhiteNoise for static files
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## 🛠 Troubleshooting

### "No such table" error
```bash
python manage.py makemigrations
python manage.py migrate
```

### "AUTH_USER_MODEL refers to an uninstalled model"
Make sure `'dms'` is in `INSTALLED_APPS` in settings.py.

### Template not found error
Verify `DIRS` in TEMPLATES points to `[BASE_DIR / 'dms' / 'templates']`.

### Media files not showing
Add to config/urls.py:
```python
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 📦 requirements.txt

```
Django>=4.2,<5.0
Pillow>=10.0.0
gunicorn>=21.0.0
whitenoise>=6.6.0
```

---

*Built to implement the Paperless Management System flowchart and use case diagram.*
