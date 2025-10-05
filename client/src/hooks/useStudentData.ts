import { useState, useCallback, useEffect } from "react";
import { fetchStudents, deleteStudent, StudentData } from "@/actions/student";
import useDebounce from "@/hooks/useDebounce";
import { toast } from "react-hot-toast";

export interface StudentFilters {
  search?: string;
  class?: string;
  status?: "" | "active" | "inactive";
  page?: number;
  pageSize?: number;
}

export const useStudentData = (
  initialFilters: Partial<StudentFilters> = {}
) => {
  const [students, setStudents] = useState<StudentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<StudentFilters>({
    search: "",
    class: "",
    status: "",
    page: 1,
    pageSize: 10,
    ...initialFilters,
  });

  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
  });

  const debouncedSearch = useDebounce(filters.search || "", 500);

  const fetchStudentList = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();

      // Add pagination
      params.append("page", String(filters.page || 1));
      params.append("page_size", String(filters.pageSize || 10));

      // Add filters if they exist
      if (debouncedSearch) params.append("search", debouncedSearch);
      if (filters.class) params.append("class", filters.class);
      if (filters.status) {
        params.append(
          "is_active",
          filters.status === "active" ? "true" : "false"
        );
      }

      const response = await fetchStudents(params.toString());

      if (response.success && response.data) {
        setStudents(response.data.results || response.data);

        // Handle pagination if available in response
        if (response.data.count !== undefined) {
          setPagination({
            currentPage: response.data?.current_page || 1,
            totalPages: response.data?.total_pages || 1,
            totalItems: response.data?.count || 0,
          });
        } else {
          // Fallback if no pagination data
          setPagination((prev) => ({
            ...prev,
            totalItems: Array.isArray(response.data) ? response.data.length : 0,
          }));
        }
      } else {
        throw new Error(response.error || "Failed to fetch students");
      }
    } catch (err: any) {
      console.error("Error fetching students:", err);
      setError(err.message || "An error occurred while fetching students");
      toast.error(err.message || "Failed to load students. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [filters, debouncedSearch]);

  const handleDeleteStudent = async (id: number) => {
    try {
      const response = await deleteStudent(id);
      if (response.success) {
        toast.success("Student deleted successfully");
        fetchStudentList(); // Refresh the list
        return true;
      } else {
        throw new Error(response.error || "Failed to delete student");
      }
    } catch (err: any) {
      console.error("Error deleting student:", err);
      toast.error(err.message || "Failed to delete student");
      return false;
    }
  };

  const updateFilters = (newFilters: Partial<StudentFilters>) => {
    setFilters((prev) => ({
      ...prev,
      ...newFilters,
      // Reset to first page when filters change
      ...(Object.keys(newFilters).some(
        (key) => key !== "page" && key !== "pageSize"
      )
        ? { page: 1 }
        : {}),
    }));
  };

  // Get unique classes for filter dropdown
  const classes = [
    ...new Set(
      students && typeof students?.map == "function"
        ? students?.map((s) =>
            typeof s.student_class === "object"
              ? s.student_class.name
              : s.student_class
          )
        : []
    ),
  ];

  // Auto-refresh when filters change
  useEffect(() => {
    fetchStudentList();
  }, [fetchStudentList]);

  return {
    students,
    loading,
    error,
    filters,
    pagination,
    classes,
    fetchStudentList,
    handleDeleteStudent,
    updateFilters,
  };
};

export default useStudentData;
