import { useState, useCallback, useEffect } from 'react';
import { fetchStaff, deleteStaff, StaffData } from '@/actions/staff';
import useDebounce from '@/hooks/useDebounce';
import { toast } from 'react-hot-toast';

export interface StaffFilters {
  search?: string;
  department?: string;
  status?: '' | 'active' | 'inactive';
  role?: '' | 'teaching' | 'non-teaching';
  page?: number;
  pageSize?: number;
}

export const useStaffData = (initialFilters: Partial<StaffFilters> = {}) => {
  const [staff, setStaff] = useState<StaffData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<StaffFilters>({
    search: '',
    department: '',
    status: '',
    role: '',
    page: 1,
    pageSize: 10,
    ...initialFilters,
  });
  
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
  });

  const debouncedSearch = useDebounce(filters.search || '', 500);

  const fetchStaffList = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      
      // Add pagination
      params.append('page', String(filters.page || 1));
      params.append('page_size', String(filters.pageSize || 10));
      
      // Add filters if they exist
      if (debouncedSearch) params.append('search', debouncedSearch);
      if (filters.department) params.append('department', filters.department);
      if (filters.status) {
        params.append('is_active', filters.status === 'active' ? 'true' : 'false');
      }
      if (filters.role) {
        params.append('is_teaching', filters.role === 'teaching' ? 'true' : 'false');
      }

      const response = await fetchStaff(params.toString());

    //   if (response.success && response.data) {
    //     setStaff(response.data.results || response.data);
        
    //     // Handle pagination if available in response
    //     if (response.data.count !== undefined) {
    //       setPagination({
    //         currentPage: response.data.current_page || 1,
    //         totalPages: response.data.total_pages || 1,
    //         totalItems: response.data.count || 0,
    //       });
    //     } else {
    //       // Fallback if no pagination data
    //       setPagination(prev => ({
    //         ...prev,
    //         totalItems: response.data.length || 0,
    //       }));
    //     }
    //   } else {
    //     throw new Error(response.error || 'Failed to fetch staff');
    //   }
    } catch (err: any) {
      console.error('Error fetching staff:', err);
      setError(err.message || 'An error occurred while fetching staff');
      toast.error(err.message || 'Failed to load staff. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters, debouncedSearch]);

  const handleDeleteStaff = async (id: number) => {
    try {
      const response = await deleteStaff(id);
      if (response.success) {
        toast.success('Staff member deleted successfully');
        fetchStaffList(); // Refresh the list
        return true;
      } else {
        throw new Error(response.error || 'Failed to delete staff member');
      }
    } catch (err: any) {
      console.error('Error deleting staff:', err);
      toast.error(err.message || 'Failed to delete staff member');
      return false;
    }
  };

  const updateFilters = (newFilters: Partial<StaffFilters>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
      // Reset to first page when filters change
      ...(Object.keys(newFilters).some(key => key !== 'page' && key !== 'pageSize')
        ? { page: 1 }
        : {}),
    }));
  };

  // Get unique departments for filter dropdown
  const departments = [...new Set(staff.map(s => s.department).filter(Boolean))];

//   // Prepare data for the table
//   const tableData = staff.map(staffMember => {
//     const user = typeof staffMember.user === 'object' ? staffMember.user : {};
//     return {
//       id: staffMember.id,
//       name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
//       email: user.email || '',
//       phone: user.phone || '',
//       department: staffMember.department || 'N/A',
//       is_teaching_staff: staffMember.is_teaching_staff,
//       is_active: user.is_active !== false, // Default to true if not specified
//       image: user.image,
//     };
//   });

  // Auto-refresh when filters change
  useEffect(() => {
    fetchStaffList();
  }, [fetchStaffList]);

//   return {
//     staff,
//     tableData,
//     loading,
//     error,
//     filters,
//     pagination,
//     departments,
//     fetchStaffList,
//     handleDeleteStaff,
//     updateFilters,
//   };
};

export default useStaffData;
