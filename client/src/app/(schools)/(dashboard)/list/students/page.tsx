"use client";

import { useEffect, useState, useCallback } from "react";
import FormModal from "@/components/FormModal";
import Table from "@/components/Table";
import TableSearch from "@/components/TableSearch";
import Image from "next/image";
import Link from "next/link";
import { useSession } from "next-auth/react";
import {
  fetchStudents,
  deleteStudent,
  StudentData,
  UserData,
} from "@/actions/student";
// import useDebounce from "@/hooks/useDebounce";
// import { formatPhoneNumber } from "@/utils/format";
import toast from "react-hot-toast";
import {
  FiFilter,
  FiSearch,
  FiUserPlus,
  FiEdit2,
  FiTrash2,
  FiEye,
} from "react-icons/fi";
import useDebounce from "@/hooks/useDebounce";
import { formatPhoneNumber } from "@/utils/format";
import useStudentData from "@/hooks/useStudentData";

const StudentListPage = () => {
  const { data: session } = useSession();
  const role = session?.user?.role || "guest";
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [regNoFilter, setregNoFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | "active" | "inactive">(
    ""
  );
  const [roleFilter, setRoleFilter] = useState<
    "" | "teaching" | "non-teaching"
  >("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [student, setStudent] = useState<any[]>([]);
  const itemsPerPage = 10;
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  const handleDelete = async (id: number) => {
    if (
      !confirm(
        "Are you sure you want to delete this student? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await deleteStudent(id);

      if (!response.success) {
        throw new Error("Failed to delete student");
      }

      await fetchStudentList();
      toast.success("Student deleted successfully");
    } catch (error: any) {
      console.error("Error deleting student:", error);
      toast.error(error.message || "Failed to delete student");
    }
  };

  type Student = {
    id: number;
    reg_no: string;
    user: {
      id: number;
      first_name: string;
      last_name: string;
      email: string;
      phone: string;
      image: string;
    };
    student_class: {
      id: number;
      name: string;
    };
    admission_date: string;
    date_of_birth: string;
  };

  const columns = [
    {
      header: "Full Name",
      accessor: "name",
      className: "hidden md:table-cell",
    },
    {
      header: "Student ID",
      accessor: "student_id",
    },
    {
      header: "Reg. Number",
      accessor: "reg_no",
      className: "hidden md:table-cell",
    },
    {
      header: "Gender",
      accessor: "gender",
      className: "hidden md:table-cell",
      cell: (row: any) =>
        row.gender == "M" ? "Male" : row.gender == "F" ? "Female" : "Other",
    },
    {
      header: "Phone",
      accessor: "phone",
      className: "hidden lg:table-cell",
    },
    {
      header: "Admission Date",
      accessor: "admission_date",
      className: "hidden lg:table-cell",
    },
    {
      header: "Actions",
      accessor: "action",
    },
  ];

  const [searchQuery, setSearchQuery] = useState("");

  const {
    students,
    loading: studentLoading,
    error,
    filters,
    pagination,
    classes,
    updateFilters,
    handleDeleteStudent,
  } = useStudentData();

  // // Update search query in filters
  // useEffect(() => {
  //   updateFilters({ search: searchQuery });
  // }, [searchQuery, updateFilters]);

  // const handlePageChange = (page: number) => {
  //   updateFilters({ page });
  // };

  // const handleClassFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
  //   updateFilters({ class: e.target.value });
  // };

  const fetchStudentList = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: itemsPerPage.toString(),
        ...(debouncedSearchTerm && { q: debouncedSearchTerm }),
        ...(regNoFilter && { department: regNoFilter }),
        ...(statusFilter && {
          is_active: statusFilter === "active" ? "true" : "false",
        }),
        ...(roleFilter && {
          is_teaching: roleFilter === "teaching" ? "true" : "false",
        }),
      });

      const response = await fetchStudents(params.toString());
      console.log(response, Array.isArray(response.data));

      if (response.success && response.data) {
        const studentData = Array.isArray(response.data)
          ? response.data
          : response.data || [];
        const totalCount = response.count || studentData.length;

        setStudent(studentData);
        setTotalPages(Math.ceil(totalCount / itemsPerPage));
        setTotalItems(totalCount);
      } else {
        throw new Error(response.error || "Failed to fetch students");
      }
    } catch (error: any) {
      console.error("Error fetching students:", error);
      toast.error(error.message || "An error occurred while fetching students");
    } finally {
      setLoading(false);
    }
  }, [
    currentPage,
    debouncedSearchTerm,
    regNoFilter,
    statusFilter,
    roleFilter,
    itemsPerPage,
  ]);

  useEffect(() => {
    fetchStudentList();
  }, [fetchStudentList]);

  // Define the columns for the table
  // const columns = [
  //   {
  //     header: "Student",
  //     accessor: "name",
  //     cell: (row: any) => (
  //       <div className="flex items-center space-x-3">
  //         <div className="avatar">
  //           <div className="mask mask-squircle w-10 h-10">
  //             <Image
  //               src={row.image || "/avatar-placeholder.png"}
  //               alt={row.name}
  //               width={40}
  //               height={40}
  //               className="rounded-full object-cover"
  //             />
  //           </div>
  //         </div>
  //         <div>
  //           <div className="font-semibold">{row.name}</div>
  //           <div className="text-xs text-gray-500">{row.email}</div>
  //         </div>
  //       </div>
  //     ),
  //   },
  //   {
  //     header: "Department",
  //     accessor: "department",
  //     className: "hidden md:table-cell",
  //   },
  //   {
  //     header: "Gender",
  //     accessor: "gender",
  //     className: "hidden md:table-cell",
  //     cell: (row: any) =>
  //       row.gender == "M" ? "Male" : row.gender == "F" ? "Female" : "Other",
  //   },
  //   {
  //     header: "Role",
  //     accessor: "role",
  //     className: "hidden lg:table-cell",
  //     cell: (row: any) => (
  //       <span
  //         className={`badge ${
  //           row.is_teaching_staff ? "badge-primary" : "badge-ghost"
  //         }`}
  //       >
  //         {row.is_teaching_staff ? "Teaching Staff" : "Non-Teaching Staff"}
  //       </span>
  //     ),
  //   },
  //   {
  //     header: "Contact",
  //     accessor: "phone",
  //     className: "hidden lg:table-cell",
  //     cell: (row: any) => (row.phone ? formatPhoneNumber(row.phone) : "N/A"),
  //   },
  //   {
  //     header: "Status",
  //     accessor: "status",
  //     className: "hidden sm:table-cell",
  //     cell: (row: any) => (
  //       <span
  //         className={`px-2 py-1 text-xs rounded-full ${
  //           row.is_active
  //             ? "bg-green-100 text-green-800"
  //             : "bg-gray-100 text-gray-800"
  //         }`}
  //       >
  //         {row.is_active ? "Active" : "Inactive"}
  //       </span>
  //     ),
  //   },
  //   ...(role === "owner" || role === "admin"
  //     ? [
  //         {
  //           header: "Actions",
  //           accessor: "actions",
  //           cell: (row: any) => (
  //             <div className="flex items-center space-x-2">
  //               <Link
  //                 href={`/list/staff/${row.id}`}
  //                 className="btn btn-ghost btn-xs"
  //               >
  //                 <FiEye className="h-4 w-4" />
  //               </Link>
  //               <FormModal
  //                 table="staff"
  //                 type="update"
  //                 id={row.id}
  //                 data={row}
  //                 onSuccess={fetchStudentList}
  //                 buttonClass="btn btn-ghost btn-xs"
  //               >
  //                 <FiEdit2 className="h-4 w-4" />
  //               </FormModal>
  //               <button
  //                 onClick={() => handleDelete(row.id)}
  //                 className="btn btn-ghost btn-xs text-error hover:bg-error/10"
  //                 title="Delete"
  //               >
  //                 <FiTrash2 className="h-4 w-4" />
  //               </button>
  //             </div>
  //           ),
  //         },
  //       ]
  //     : []),
  // ];

  // // Get unique departments for filter
  // const departments = [
  //   ...new Set(students.map((s) => s.department).filter(Boolean)),
  // ];

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearchTerm, regNoFilter, statusFilter, roleFilter]);

  // Prepare data for the table
  const tableData = students.map((studentMember) => {
    const user =
      typeof studentMember.user === "object"
        ? studentMember.user
        : ({} as UserData);

    return {
      id: studentMember.id,
      name: `${user.first_name || ""} ${user.last_name || ""}`.trim(),
      date_of_birth: studentMember.date_of_birth || "N/A",
      email: user.email || "",
      phone: user.phone || "",
      reg_no: studentMember.reg_no || "N/A",
      student_id: studentMember.student_id || "N/A",
      admission_date: studentMember.admission_date || "N/A",
      is_active: user.is_active !== false, // Default to true if not specified
      image: user.image,
      gender: user?.gender || "",
      session_admitted: studentMember.session_admitted || "N/A",
    };
  });

  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Student Management
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {totalItems} {totalItems === 1 ? "student" : "students"} found
          </p>
        </div>

        {["admin", "owner"].includes(role) && (
          <FormModal
            table="student"
            type="create"
            onSuccess={fetchStudentList}
            buttonClass="btn btn-primary gap-2"
          >
            <FiUserPlus className="h-4 w-4" />
            Add New Student
          </FormModal>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FiSearch className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search by name, email, or department..."
              className="input input-bordered w-full pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Department Filter */}
          {/* <select
            className="select select-bordered w-full"
            value={regNoFilter}
            onChange={(e) => setregNoFilter(e.target.value)}
          >
            <option value="">All Departments</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select> */}

          {/* Status Filter */}
          <select
            className="ml-auto select select-bordered w-full"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>

          {/* Role Filter */}
          {/* <select
            className="select select-bordered w-full"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as any)}
          >
            <option value="">All Roles</option>
            <option value="teaching">Teaching Student</option>
            <option value="non-teaching">Non-Teaching Student</option>
          </select> */}
        </div>
      </div>

      {/* Staff Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center p-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : student.length === 0 ? (
          <div className="text-center p-12">
            <div className="mx-auto w-16 h-16 text-gray-300 mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                className="w-full h-full"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            </div>
            <h3 className="flex gap-3 justify-center align-center text-lg font-medium text-gray-900 mb-2">
              <span> No student found</span>
              {!debouncedSearchTerm &&
                !regNoFilter &&
                !statusFilter &&
                !roleFilter &&
                ["admin", "owner"].includes(role) && (
                  <FormModal
                    table="student"
                    type="create"
                    onSuccess={fetchStudentList}
                    buttonClass="btn btn-primary gap-2"
                  >
                    <FiUserPlus className="h-4 w-4" />
                    Add Student
                  </FormModal>
                )}
            </h3>
            <p className="text-gray-500 mb-4">
              {debouncedSearchTerm || regNoFilter || statusFilter || roleFilter
                ? "Try adjusting your search or filter to find what you're looking for."
                : "Get started by adding a new student."}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table
                columns={columns}
                data={tableData}
                keyField="id"
                emptyMessage="No Student found"
                className="w-full"
                rowClassName="hover:bg-gray-50"
              />
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
                <div className="text-sm text-gray-500">
                  Showing{" "}
                  <span className="font-medium">
                    {(currentPage - 1) * itemsPerPage + 1}
                  </span>{" "}
                  to{" "}
                  <span className="font-medium">
                    {Math.min(currentPage * itemsPerPage, totalItems)}
                  </span>{" "}
                  of <span className="font-medium">{totalItems}</span> results
                </div>
                <div className="join">
                  <button
                    className="join-item btn btn-sm"
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                  >
                    «
                  </button>
                  <button className="join-item btn btn-sm">
                    Page {currentPage}
                  </button>
                  <button
                    className="join-item btn btn-sm"
                    onClick={() =>
                      setCurrentPage((p) => Math.min(totalPages, p + 1))
                    }
                    disabled={currentPage === totalPages}
                  >
                    »
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default StudentListPage;
