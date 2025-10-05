"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import InputField from "../InputField";
import Image from "next/image";
import toast from "react-hot-toast";
import { CircleUserRound } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { UserData, createStaff, updateStaff, StaffData } from "@/actions/staff";

// Define the form schema using Zod
const staffFormSchema = z.object({
  email: z.string().email({ message: "Invalid email address!" }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters long!" })
    .optional()
    .or(z.literal("")),
  first_name: z.string().min(1, { message: "First name is required!" }),
  last_name: z.string().min(1, { message: "Last name is required!" }),
  phone: z.string().optional(),
  department: z.string().min(1, { message: "Department is required!" }),
  gender: z.enum(["M", "F"], { message: "Gender is required!" }),
  is_teaching_staff: z.boolean().default(false),
  // image: z.any().optional(),
});

// Extract the type from the schema
export type Inputs = z.infer<typeof staffFormSchema>;

// Define the props interface
interface StaffFormProps {
  type: "create" | "update" | "delete";
  initialData?: Partial<StaffData> & { id?: number };
  onSuccess?: () => void;
}

const StaffForm = ({
  type,
  initialData: data = {},
  onSuccess,
}: StaffFormProps) => {
  const [imagePreview, setImagePreview] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<Inputs>({
    resolver: zodResolver(staffFormSchema),
    defaultValues: data
      ? {
          ...data,
          ...(typeof data.user === "object" &&
            data.user !== null &&
            data.user !== undefined && {
              first_name: data.user.first_name || "",
              last_name: data.user.last_name || "",
              email: data.user.email || "",
              phone: data.user.phone || "",
              gender: data.user.gender || "M",
              is_teaching_staff: data.is_teaching_staff || false,
              // image: data.user.image || null,
            }),
        }
      : {
          gender: "M",
          is_teaching_staff: false,
        },
  });

  const handleCreateStaff = async () => {
    try {
      const response = await createStaff(data);
      if (response.success) {
        toast.success("Staff member created successfully");
        // onSuccess?.();
      } else {
        throw new Error(response.error || "Failed to create staff member");
      }
    } catch (error: any) {
      console.error("Error creating staff:", error);
      toast.error(error.message || "Failed to create staff member");
    }
  };

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === "string") {
          setImagePreview(reader.result);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const onSubmit = async (formData: Inputs) => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      const staffData: StaffData = {
        ...formData,
        user: {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone: formData.phone,
          gender: formData.gender,
          // image: formData.image,
        },
        department: formData.department,
        is_teaching_staff: formData.is_teaching_staff,
      };

      if (type === "create") {
        const user = staffData.user as UserData;
        user.password = formData.password || "defaultPassword123!";
        staffData.user = user;
      }

      let response;
      if (type === "create") {
        response = await createStaff(staffData);
      } else if (data?.id) {
        response = await updateStaff(data.id, staffData);
      } else {
        throw new Error("Staff ID is required for updates");
      }

      console.log("response for type", type, response);

      if (response.success) {
        toast.success(
          `Staff ${type === "create" ? "created" : "updated"} successfully!`
        );
        // onSuccess?.();
        if (type === "create") {
          reset();
          setImagePreview("");
        }
      } else {
        throw new Error(response.error || "An error occurred");
      }
    } catch (error: any) {
      console.error("Error:", error);
      const errorMessage =
        error?.response?.data?.message || error.message || "An error occurred";
      toast.error(
        `Failed to ${
          type === "create" ? "create" : "update"
        } staff: ${errorMessage}`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="flex flex-col gap-8" onSubmit={handleSubmit(onSubmit)}>
      <h1 className="text-xl font-semibold">
        {type === "create" ? "Create a new staff" : "Update staff"}
      </h1>

      <span className="text-xs text-gray-400 font-medium">
        Authentication Information
      </span>
      <div className="flex justify-between flex-wrap gap-4">
        <InputField
          label="Email"
          name="email"
          type="email"
          register={register}
          error={errors.email}
          disabled={isSubmitting}
        />
        {type === "create" && (
          <InputField
            label="Password"
            name="password"
            type="password"
            register={register}
            error={errors.password}
            disabled={isSubmitting}
            placeholder="Leave blank for auto-generated"
          />
        )}
      </div>

      <span className="text-xs text-gray-400 font-medium">
        Personal Information
      </span>
      <div className="flex justify-between flex-wrap gap-4">
        <InputField
          label="First Name"
          name="first_name"
          register={register}
          error={errors.first_name}
          disabled={isSubmitting}
        />
        <InputField
          label="Last Name"
          name="last_name"
          register={register}
          error={errors.last_name}
          disabled={isSubmitting}
        />
        <InputField
          label="Phone"
          name="phone"
          register={register}
          error={errors.phone}
          disabled={isSubmitting}
        />
        <InputField
          label="Department"
          name="department"
          register={register}
          error={errors.department}
          disabled={isSubmitting}
        />

        <div className="flex flex-col gap-2 w-full md:w-1/4">
          <label className="text-xs text-gray-500">Gender</label>
          <select
            className="ring-[1.5px] ring-gray-300 p-2 rounded-md text-sm w-full"
            {...register("gender")}
            disabled={isSubmitting}
          >
            <option value="M">Male</option>
            <option value="F">Female</option>
          </select>
          {errors.gender?.message && (
            <p className="text-xs text-red-400">
              {errors.gender.message.toString()}
            </p>
          )}
        </div>

        <div className="flex items-center gap-4 w-full md:w-1/4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              {...register("is_teaching_staff")}
              className="rounded border-gray-300 text-blue-600"
              disabled={isSubmitting}
            />
            Teaching Staff
          </label>
        </div>

        {/* <div className="flex flex-col gap-2 w-full md:w-1/4 justify-center">
          <label
            className="text-xs text-gray-500 flex items-center gap-2 cursor-pointer"
            htmlFor="image-upload"
          >
            <Image src="/upload.png" alt="" width={28} height={28} />
            <span>Upload a photo</span>
          </label>
          <input
            type="file"
            id="image-upload"
            accept="image/*"
            className="hidden"
            {...register("image")}
            onChange={handleImageChange}
            disabled={isSubmitting}
          />
          {errors.image?.message && (
            <p className="text-xs text-red-400">
              {errors.image.message.toString()}
            </p>
          )}
        </div> */}
      </div>

      <div className="flex justify-center">
        {imagePreview ? (
          <img
            src={imagePreview}
            alt="Preview"
            className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
          />
        ) : typeof data.user == "object" && data?.user?.image ? (
          <img
            src={data?.user?.image as string}
            alt="Current"
            className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
          />
        ) : (
          <div className="w-24 h-24 rounded-full bg-gray-100 flex items-center justify-center">
            <CircleUserRound size={48} className="text-gray-400" />
          </div>
        )}
      </div>

      <button
        type="submit"
        className={`bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors ${
          isSubmitting ? "opacity-50 cursor-not-allowed" : ""
        }`}
        disabled={isSubmitting}
      >
        {isSubmitting
          ? "Processing..."
          : type === "create"
          ? "Create Staff"
          : "Update Staff"}
      </button>
    </form>
  );
};

export default StaffForm;
