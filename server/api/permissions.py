from rest_framework import permissions

class IsSuperAdminOrReadOnly(permissions.BasePermission):
  def has_permission(self, request, view):
    if request.method in permissions.SAFE_METHODS:
      return True
    return bool(request.user and request.user.is_superadmin)
  
class IsAdminOrReadOnly(permissions.BasePermission):
  def has_permission(self, request, view):
    if request.method in permissions.SAFE_METHODS:

      return True 
    return bool(request.user and request.user.is_admin)
  
class IsStudent(permissions.BasePermission):
  def has_permission(self, request, view):
    if request.method in permissions.SAFE_METHODS:
      return True
    return bool(request.user and request.user.is_student)

class IsAdminOrIsStaffOrReadOnly(permissions.BasePermission):
  def has_permission(self, request, view):
    if request.method in permissions.SAFE_METHODS:
      return True
    return bool(request.user and request.user.is_admin|request.user.is_staff)

class IsAuthenticatedEmployee(permissions.BasePermission):
    """
    Allows access only to authenticated employees.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'employee'))


class IsHRAdmin(permissions.BasePermission):
    """
    Allows access only to HR admins.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'employee') and
            request.user.has_perm('attendance.view_attendance')
        )


class IsManagerOrHR(permissions.BasePermission):
    """
    Allows access only to managers or HR admins.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and hasattr(request.user, 'employee')):
            return False
            
        # Check if user is HR admin
        if request.user.has_perm('attendance.view_attendance'):
            return True
            
        # Check if user is a manager
        if hasattr(request.user.employee, 'employee_work_info') and \
           request.user.employee.employee_work_info.reporting_manager:
            return True
            
        return False


class CanManageAttendance(permissions.BasePermission):
    """
    Allows access to manage attendance records.
    HR can manage all, managers can manage their team, employees can manage their own.
    """
    def has_object_permission(self, request, view, obj):
        # HR can manage all
        if request.user.has_perm('attendance.manage_attendance'):
            return True
            
        # Managers can manage their team
        if hasattr(request.user, 'employee') and hasattr(request.user.employee, 'employee_work_info'):
            if obj.employee_id.employee_work_info.reporting_manager == request.user.employee:
                return True
                
        # Employees can manage their own
        if hasattr(obj.employee_id, 'employee_user') and obj.employee_id.employee_user == request.user:
            return True
            
        return False


class CanViewAttendance(permissions.BasePermission):
    """
    Allows viewing attendance records.
    HR can view all, managers can view their team's, employees can view their own.
    """
    def has_permission(self, request, view):
        # HR can view all
        if request.user.has_perm('attendance.view_attendance'):
            return True
            
        # Managers can view their team's attendance
        if hasattr(request.user, 'employee') and hasattr(request.user.employee, 'employee_work_info'):
            if request.user.employee.employee_work_info.reporting_manager:
                return True
                
        # Employees can view their own
        return True  # The view will filter the queryset based on the user

    def has_object_permission(self, request, view, obj):
        # HR can view all
        if request.user.has_perm('attendance.view_attendance'):
            return True
            
        # Managers can view their team's attendance
        if hasattr(request.user, 'employee') and hasattr(request.user.employee, 'employee_work_info'):
            if obj.employee_id.employee_work_info.reporting_manager == request.user.employee:
                return True
                
        # Employees can view their own
        if hasattr(obj.employee_id, 'employee_user') and obj.employee_id.employee_user == request.user:
            return True
            
        return False