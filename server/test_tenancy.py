"""
Test script to verify multi-tenancy and audit logging functionality.
Run with: python manage.py shell < test_tenancy.py
"""
import os
import django

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CONFIG.settings')
    django.setup()

def test_rojitech_manager():
    """Test the RojitechManager functionality"""
    from main.models import School, User, get_current_school, set_current_school
    from django.contrib.auth import get_user_model
    
    print("\n=== Testing RojitechManager ===")
    
    # Get or create test schools
    User = get_user_model()
    
    # Create test users first with unique login_emails
    import time
    timestamp = int(time.time())
    
    # Create first owner
    owner1_login_email = f'testowner1_{timestamp}@example.com'
    try:
        owner1 = User.objects.get(login_email=owner1_login_email)
    except User.DoesNotExist:
        owner1 = User.objects.create(
            login_email=owner1_login_email,
            email=f'owner1_{timestamp}@example.com',
            role='owner',
            is_active=True,
            first_name='Test',
            last_name='Owner1'
        )
        owner1.set_password('testpass123')
        owner1.save()
    
    # Create second owner with a different email
    owner2_login_email = f'testowner2_{timestamp}@example.com'
    try:
        owner2 = User.objects.get(login_email=owner2_login_email)
    except User.DoesNotExist:
        owner2 = User.objects.create(
            login_email=owner2_login_email,
            email=f'owner2_{timestamp}@example.com',
            role='owner',
            is_active=True,
            first_name='Test',
            last_name='Owner2'
        )
        owner2.set_password('testpass123')
        owner2.save()
    
    # Create test schools
    school1_name = 'Test School 1'
    try:
        school1 = School.objects.get(name=school1_name)
    except School.DoesNotExist:
        school1 = School.objects.create(
            name=school1_name,
            email='test1@example.com',
            phone='1234567890',
            address='123 Test St',
            owner=owner1
        )
    
    school2_name = 'Test School 2'
    try:
        school2 = School.objects.get(name=school2_name)
    except School.DoesNotExist:
        school2 = School.objects.create(
            name=school2_name,
            email='test2@example.com',
            phone='0987654321',
            address='456 Test Ave',
            owner=owner2
        )
    
    # Test thread-local school context
    print("\nTesting thread-local school context...")
    set_current_school(school1.id)
    current_school = get_current_school()
    print(f"Current school set to: {current_school}")
    assert current_school == school1.id, "Failed to set/get current school"
    
    # Test manager filtering
    print("\nTesting manager filtering...")
    from main.models import ClassList
    
    # Create test classes in both schools
    class1 = ClassList.objects.create(name="Class A", school=school1)
    class2 = ClassList.objects.create(name="Class B", school=school2)
    
    # Test default manager (should respect current school)
    set_current_school(school1.id)
    classes = ClassList.objects.all()
    print(f"Classes in {school1.name}: {list(classes)}")
    assert class1 in classes, f"Class1 not found in {school1.name}"
    assert class2 not in classes, f"Class2 should not be in {school1.name}"

    # Test explicit school filtering
    classes_school2 = ClassList.rojitech_objects.for_school(school2.id)
    print(f"Classes in {school2.name}: {list(classes_school2)}")
    assert class2 in classes_school2, f"Class2 not found in {school2.name}"
    assert class1 not in classes_school2, f"Class1 should not be in {school2.name}"
    
    print("\n✅ RojitechManager tests passed!")

def test_audit_logging():
    """Test audit logging functionality"""
    from main.models import AuditLog, User, School
    from django.contrib.auth import get_user_model

    print("\n=== Testing Audit Logging ===")

    # Get or create test data
    User = get_user_model()

    # Create test user if it doesn't exist
    user_email = 'testuser@example.com'
    try:
        user = User.objects.get(login_email=user_email)
    except User.DoesNotExist:
        user = User.objects.create(
            login_email=user_email,
            email='test@example.com',
            role='admin',
            is_active=True,
            first_name='Test',
            last_name='User'
        )
        user.set_password('testpass123')
        user.save()

    # Get or create a school
    school = School.objects.first()
    if not school:
        print("No schools found, creating a test school...")
        school = School.objects.create(
            name="Test School",
            code="TEST",
            email="test@example.com",
            phone="1234567890",
            address="123 Test St",
            owner=user
        )

    # Test creating an audit log entry
    print("\nTesting audit log creation...")
    log_entry = AuditLog.objects.create(
        user=user,
        action=AuditLog.ACTION_CREATE,
        model="TestModel",
        object_id="123",
        changes={"field": "old_value", "new_field": "new_value"},
        ip_address="127.0.0.1"
    )
    
    print(f"Created audit log: {log_entry}")
    assert log_entry.id is not None, "Failed to create audit log"
    assert log_entry.timestamp is not None, "Audit log missing timestamp"
    
    # Test log_action utility
    from main.audit_utils import log_action
    
    print("\nTesting log_action utility...")
    log_entry = log_action(
        user=user,
        action=AuditLog.ACTION_UPDATE,
        model="TestModel",
        object_id="123",
        changes={"field": "updated_value"},
        request=None
    )
    
    print(f"Logged action: {log_entry.action} on {log_entry.model}")
    assert log_entry.action == AuditLog.ACTION_UPDATE, "Incorrect action logged"
    
    print("\n✅ Audit logging tests passed!")

def test_tenant_middleware():
    """Test tenant middleware functionality"""
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    from main.middleware import TenantMiddleware
    from main.models import School, get_current_school_id as get_current_school
    
    print("\n=== Testing Tenant Middleware ===")
    
    # Setup test data
    User = get_user_model()
    
    # Create test user if it doesn't exist
    user_email = 'test_middleware@example.com'
    try:
        user = User.objects.get(login_email=user_email)
    except User.DoesNotExist:
        user = User.objects.create(
            login_email=user_email,
            email='test_middleware@example.com',
            role='admin',
            is_active=True,
            first_name='Test',
            last_name='Middleware'
        )
        user.set_password('testpass123')
        user.save()
    
    # Get or create a school
    school = School.objects.first()
    if not school:
        print("No schools found, creating a test school...")
        school = School.objects.create(
            name="Test School Middleware",
            code="TSM",
            email="test_middleware@example.com",
            phone="1234567890",
            address="123 Test St",
            owner=user
        )
    
    # Simulate a request
    factory = RequestFactory()
    request = factory.get('/test/')
    request.user = user
    request.session = {}
    
    # Set user's school
    user.school = school
    user.save()
    
    # Process the request through the middleware
    middleware = TenantMiddleware(lambda r: None)  # Dummy response function
    
    print("\nProcessing request with middleware...")
    middleware.process_request(request)
    
    # Verify school was set in thread local storage
    current_school = get_current_school()
    print(f"Current school from middleware: {current_school}")
    assert current_school == school.id, "Middleware failed to set school context"
    
    print("\n✅ Tenant middleware tests passed!")

if __name__ == "__main__":
    setup_django()
    
    print("=== Starting Multi-tenancy and Audit Logging Tests ===\n")
    
    try:
        test_rojitech_manager()
        test_audit_logging()
        test_tenant_middleware()
        
        print("\n=== All tests passed successfully! ===")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
