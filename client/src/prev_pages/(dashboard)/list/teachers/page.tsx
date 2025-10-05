// "use client";

// import { useEffect, useState } from "react";
// import FormModal from "@/components/FormModal";
// import Pagination from "@/components/Pagination";
// import Table from "@/components/Table";
// import TableSearch from "@/components/TableSearch";
// import Image from "next/image";
// import Link from "next/link";
// import { useSession } from "next-auth/react";
// import axiosInstance from "@/utils/axiosInstance";
// import { getApiUrl } from "@/lib/utils";

// type Teacher = {
//   id: number;
//   teacherId: string;
//   name: string;
//   email?: string;
//   photo: string;
//   phone: string;
//   subjects: string[];
//   classes: string[];
//   address: string;
// };

// const columns = [
//   {
//     header: "Info",
//     accessor: "info",
//   },
//   {
//     header: "Teacher ID",
//     accessor: "teacherId",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Department",
//     accessor: "subjects",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Classes",
//     accessor: "classes",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Phone",
//     accessor: "phone",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Address",
//     accessor: "address",
//     className: "hidden md:table-cell",
//   },
//   {
//     header: "Actions",
//     accessor: "action",
//   },
// ];

// const TeacherListPage = () => {
//   const { data: session } = useSession();
//   const role = session?.user?.role || "guest";
//   const [teachers, setTeachers] = useState<Teacher[]>([]);
//   const [loading, setLoading] = useState(true);

//   const fetchTeachers = async () => {
//     try {
//       const url = `${getApiUrl("/staff/")}`;
//       const response = await axiosInstance.get(url);
//       console.log(url);
//       console.log(response.data);
//       const formattedTeachers = response.data.map((teacher: any) => ({
//         id: teacher.id,
//         teacherId: teacher.user.id.toString(),
//         name: `${teacher.user.first_name} ${teacher.user.last_name}`,
//         email: teacher.user.email,
//         photo: teacher.user.image || "/avatar.png",
//         phone: teacher.user.phone,
//         department: teacher.department,
//         subjects: [teacher.department, ""],
//         classes: [],
//         address: "",
//       }));
//       setTeachers(formattedTeachers);
//     } catch (error: any) {
//       console.warn("Error fetching teachers:", error);
//       console.warn("Error fetching teachers:", error?.response);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchTeachers();
//   }, []);

//   const renderRow = (item: Teacher) => (
//     <tr
//       key={item?.id}
//       className="border-b border-gray-200 even:bg-slate-50 text-sm hover:bg-schPurpleLight"
//     >
//       <td className="flex items-center gap-4 p-4">
//         <Image
//           src={item?.photo}
//           alt=""
//           width={30}
//           height={30}
//           className="md:hidden xl:block w-10 h-10 rounded-full object-cover"
//         />
//         <div className="flex flex-col">
//           <h3 className="font-semibold">{item.name}</h3>
//           <p className="text-xs text-gray-500">{item?.email}</p>
//         </div>
//       </td>
//       <td className="hidden md:table-cell">{item?.teacherId}</td>
//       <td className="hidden md:table-cell">{item?.subjects?.join(",")}</td>
//       <td className="hidden md:table-cell">{item?.classes?.join(",")}</td>
//       <td className="hidden md:table-cell">{item?.phone}</td>
//       <td className="hidden md:table-cell">{item?.address}</td>
//       <td>
//         <div className="flex items-center gap-2">
//           <Link title="View" href={`/list/staff/${item.id}`}>
//             <button className="w-7 h-7 flex items-center justify-center rounded-full bg-schSky">
//               <Image src="/view.png" alt="" width={16} height={16} />
//             </button>
//           </Link>
//           {role === "admin" && (
//             <>
//               <FormModal
//                 table="staff"
//                 type="delete"
//                 id={item.id}
//                 onSuccess={fetchTeachers}
//                 moreInfo={`( ${item?.name} )`}
//               />
//             </>
//           )}
//         </div>
//       </td>
//     </tr>
//   );

//   return (
//     <div className="bg-white p-4 rounded-md flex-1 m-4 mt-0">
//       <div className="flex items-center justify-between">
//         <h1 className="hidden md:block text-lg font-semibold">All Teachers</h1>
//         <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
//           <TableSearch />
//           <div className="flex items-center gap-4 self-end">
//             <button className="w-8 h-8 flex items-center justify-center rounded-full bg-schYellow">
//               <Image src="/filter.png" alt="" width={14} height={14} />
//             </button>
//             <button className="w-8 h-8 flex items-center justify-center rounded-full bg-schYellow">
//               <Image src="/sort.png" alt="" width={14} height={14} />
//             </button>

//             {role === "admin" && (
//               <>
//                 <FormModal
//                   table="staff"
//                   type="create"
//                   onSuccess={fetchTeachers}
//                 />
//               </>
//             )}
//           </div>
//         </div>
//       </div>
//       {loading ? (
//         <div className="flex justify-center items-center h-64">
//           <p>Loading...</p>
//         </div>
//       ) : (
//         <div className="max-h-[75vh] lg:max-h-[78vh] mt-3 overflow-y-auto">
//           <Table columns={columns} data={teachers} />
//         </div>
//       )}
//       {/* <Pagination /> */}
//     </div>
//   );
// };

// export default TeacherListPage;
