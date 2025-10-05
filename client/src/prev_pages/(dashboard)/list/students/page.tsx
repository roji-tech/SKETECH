// "use client";

// import { useState, useEffect } from "react";
// import FormModal from "@/components/FormModal";
// import Pagination from "@/components/Pagination";
// import Table from "@/components/Table";
// import TableSearch from "@/components/TableSearch";
// import axiosInstance from "@/utils/axiosInstance";
// import Image from "next/image";
// import Link from "next/link";
// import { useSession } from "next-auth/react";
// import { getApiUrl } from "@/lib/utils";

// type Student = {
//   id: number;
//   studentId: string;
//   name: string;
//   email?: string;
//   photo: string;
//   phone?: string;
//   grade: number;
//   className: string; // Renamed to match API field
//   address: string;
// };

// const columns = [
//   {
//     header: "Info",
//     accessor: "info",
//   },
//   {
//     header: "Student ID",
//     accessor: "studentId",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Grade",
//     accessor: "grade",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Phone",
//     accessor: "phone",
//     className: "hidden lg:table-cell",
//   },
//   {
//     header: "Address",
//     accessor: "address",
//     className: "hidden lg:table-cell",
//   },
//   {
//     header: "Actions",
//     accessor: "action",
//   },
// ];

// const StudentListPage = () => {
//   const [students, setStudents] = useState<Student[]>([]);
//   const [isLoading, setIsLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [searchQuery, setSearchQuery] = useState("");
//   const [currentPage, setCurrentPage] = useState(1);
//   const [totalPages, setTotalPages] = useState(1);
//   const { data: session } = useSession();

//   const fetchStudents = async () => {
//     try {
//       // const response = await axiosInstance.get(url, {
//       //   params: { q: searchQuery, page: currentPage },
//       // });
//       // const { results, total_pages } = response.data;
//       // setStudents(results);
//       // setTotalPages(total_pages);

//       setIsLoading(true);
//       const url = `${getApiUrl("/students/")}`;

//       const response = await axiosInstance.get(url);
//       console.log(response.data);
//       console.log(url);

//       const formattedStudents = response.data.map((student: any) => ({
//         id: student.id,
//         studentId: student.user.id.toString(),
//         name: `${student.user.first_name} ${student.user.last_name}`,
//         email: student.user.email,
//         photo: student.user.image || "/avatar.png",
//         phone: student.user.phone,
//         department: student.department,
//         className: student.student_class,
//         address: student.user.address || "",
//       }));

//       console.log(formattedStudents);
//       setStudents(formattedStudents);
//     } catch (error: any) {
//       setError(error?.message || "Something went wrong.");
//       console.warn("Error fetching teachers:", error);
//       console.warn("Error fetching teachers:", error?.response);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchStudents();
//   }, [searchQuery, currentPage]);

//   const renderRow = (item: Student) => (
//     <tr
//       key={`${item.id}+${item.studentId}`}
//       className="border-b border-gray-200 even:bg-slate-50 text-sm hover:bg-schPurpleLight"
//     >
//       <td className="flex items-center gap-4 p-4">
//         <Image
//           src={item.photo}
//           alt={item.name}
//           width={40}
//           height={40}
//           className="md:hidden xl:block w-10 h-10 rounded-full object-cover"
//         />
//         <div className="flex flex-col">
//           <h3 className="font-semibold">{item.name}</h3>
//           <p className="text-xs text-gray-500">{item.className}</p>
//         </div>
//       </td>
//       <td className="hidden md:table-cell">{item.studentId}</td>
//       <td className="hidden md:table-cell">{item.grade}</td>
//       <td className="hidden md:table-cell">{item.phone}</td>
//       <td className="hidden md:table-cell">{item.address}</td>
//       <td>
//         <div className="flex items-center gap-2">
//           <Link href={`/list/staff/${item.id}`}>
//             <button className="w-7 h-7 flex items-center justify-center rounded-full bg-schSky">
//               <Image src="/view.png" alt="View" width={16} height={16} />
//             </button>
//           </Link>
//           {session?.user?.role === "admin" && (
//             <FormModal
//               table="student"
//               type="delete"
//               id={item.id}
//               onSuccess={fetchStudents}
//             />
//           )}
//         </div>
//       </td>
//     </tr>
//   );

//   return (
//     <div className="bg-white p-4 rounded-md flex-1 m-4 mt-0">
//       {/* TOP */}
//       <div className="flex items-center justify-between">
//         <h1 className="hidden md:block text-lg font-semibold">All Students</h1>
//         <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
//           <TableSearch onSearch={setSearchQuery} />
//           <div className="flex items-center gap-4 self-end">
//             <button className="w-8 h-8 flex items-center justify-center rounded-full bg-schYellow">
//               <Image src="/filter.png" alt="Filter" width={14} height={14} />
//             </button>
//             <button className="w-8 h-8 flex items-center justify-center rounded-full bg-schYellow">
//               <Image src="/sort.png" alt="Sort" width={14} height={14} />
//             </button>
//             {session?.user?.role === "admin" && (
//               <FormModal
//                 table="student"
//                 type="create"
//                 onSuccess={fetchStudents}
//               />
//             )}
//           </div>
//         </div>
//       </div>
//       {/* LIST */}
//       {isLoading ? (
//         <p>Loading...</p>
//       ) : (
//         <Table columns={columns} data={students} />
//       )}
//       {/* PAGINATION */}
//       {/* <Pagination
//         currentPage={currentPage}
//         totalPages={totalPages}
//         onPageChange={setCurrentPage}
//       /> */}
//     </div>
//   );
// };

// export default StudentListPage;
