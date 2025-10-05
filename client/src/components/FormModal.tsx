"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { ReactNode, useState } from "react";

// USE LAZY LOADING
const StaffForm = dynamic(() => import("./forms/StaffForm"), {
  loading: () => <h1>Loading...</h1>,
});
const StudentForm = dynamic(() => import("./forms/StudentForm"), {
  loading: () => <h1>Loading...</h1>,
});
const AnnouncementForm = dynamic(() => import("./forms/AnnouncementForm"), {
  loading: () => <h1>Loading...</h1>,
});

type TableType =
  | "staff"
  | "student"
  | "parent"
  | "subject"
  | "class"
  | "lesson"
  | "exam"
  | "assignment"
  | "result"
  | "attendance"
  | "event"
  | "announcement";

export type FormType = "create" | "update" | "delete";

interface FormModalProps {
  table: TableType;
  type: FormType;
  data?: any;
  id?: number;
  onSuccess?: () => Promise<void> | void;
  moreInfo?: string | ReactNode;
  deleteBtnText?: string;
  buttonClass?: string;
  children?: ReactNode;
}

const forms: {
  [key in TableType]?: (
    type: FormType,
    data?: any,
    onSuccess?: () => Promise<void> | void
  ) => JSX.Element;
} = {
  staff: (type, data, onSuccess) => (
    <StaffForm type={type} initialData={data} onSuccess={onSuccess} />
  ),
  student: (type, data, onSuccess) => (
    <StudentForm type={type} data={data} onSuccess={onSuccess} />
  ),
  announcement: (type, data, onSuccess) => (
    <AnnouncementForm type={type} data={data} onSuccess={onSuccess} />
  ),
};

const FormModal = ({
  table,
  type,
  data,
  id,
  onSuccess,
  moreInfo = "",
  deleteBtnText: buttonText,
  buttonClass,
  children,
}: FormModalProps) => {
  const size = type === "create" ? "w-8 h-8" : "w-7 h-7";
  const bgColor =
    type === "create"
      ? "bg-schYellow"
      : type === "update"
      ? "bg-schSky"
      : "bg-schPurple";

  const [open, setOpen] = useState(false);

  const handleSuccess = async () => {
    setOpen(false);
    if (onSuccess) {
      await onSuccess();
    }
  };

  const handleDelete = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      if (onSuccess) {
        await onSuccess();
      }
      setOpen(false);
    } catch (error) {
      console.error("Error deleting item:", error);
    }
  };

  const Form = () => {
    if (type === "delete" && id) {
      return (
        <form onSubmit={handleDelete} className="p-4 flex flex-col gap-4">
          <span className="text-center font-medium">
            All data will be lost. Are you sure you want to delete this {table}?
            &nbsp; {moreInfo}
          </span>
          <button className={buttonClass || "bg-red-700 text-white py-2 px-4 rounded-md border-none w-max self-center"}>
            {buttonText || "Delete"}
          </button>
        </form>
      );
    }

    const FormComponent = forms[table];
    if (!FormComponent) return <div>No form available for {table}</div>;

    return FormComponent(type, data, handleSuccess);
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={`${bgColor} rounded-full p-1 flex items-center justify-center`}
        title={type.charAt(0).toUpperCase() + type.slice(1)}
      >
        <Image
          src={`/${type}.png`}
          alt={type}
          width={16}
          height={16}
          className="invert"
        />
      </button>
      {open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">
                {type.charAt(0).toUpperCase() + type.slice(1)} {table}
              </h2>
              <button
                onClick={() => setOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <Form />
            {children}
          </div>
        </div>
      )}
    </>
  );
};

export default FormModal;
