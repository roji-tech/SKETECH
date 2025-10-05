"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import InputField from "../InputField";
import Image from "next/image";
import toast from "react-hot-toast";
import { CircleUserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/compat/router";
import { MyFormProps } from "@/types/intefaces";
import { getApiUrl } from "@/lib/utils";
import { apiGet, apiPost, apiPut } from "@/actions/fetchApi";

const schema = z.object({
  // username: z
  //   .string()
  //   .min(3, { message: "Username must be at least 3 characters long!" })
  //   .max(20, { message: "Username must be at most 20 characters long!" }),
  email: z.string().email({ message: "Invalid email address!" }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters long!" })
    .optional(),
  firstName: z.string().min(1, { message: "First name is required!" }),
  lastName: z.string().min(1, { message: "Last name is required!" }),
  // phone: z.string().optional(),
  gender: z.enum(["M", "F"], { message: "Gender is required!" }),
  image: z.any().optional(), // Image is optional

  reg_no: z.string().min(1, { message: "Registration number is required!" }),
  session_admitted: z
    .string()
    .min(1, { message: "Session admitted is required!" })
    .optional(), // optional
  admission_date: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), {
      message: "Invalid admission date!",
    })
    .optional(), // optional
  date_of_birth: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), {
      message: "Invalid date of birth!",
    })
    .optional(), // optional
  // student_class: z.string().min(1, { message: "Student class is required!" }).optional(),
});

type Inputs = z.infer<typeof schema>;

type ClassData = {
  id: number;
  name: string;
  name_display: string;
};

const StudentForm = ({
  type,
  data,
  onSuccess: successFunction,
}: MyFormProps) => {
  const [imagePreview, setImagePreview] = useState("");
  const [classes, setClasses] = useState<ClassData[]>([]); // Type for classes state
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Inputs>({
    resolver: zodResolver(schema),
    defaultValues: data || {},
  });

  const handleImageChange = (event: any) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader?.result === "string") {
          setImagePreview(reader.result); // Update state with the image URL
        }
      };
      reader.readAsDataURL(file); // Read the file as a data URL
    }
  };

  const onSubmit = handleSubmit(async (formData) => {
    const requestData = new FormData();
    // requestData.append("user.username", formData.username);
    requestData.append("user.email", formData.email);
    if (type === "create") {
      requestData.append("user.password", formData.password!); // Only include password on creation
    }
    requestData.append("user.first_name", formData.firstName);
    requestData.append("user.last_name", formData.lastName);
    // requestData.append("user.phone", formData.phone || "");
    requestData.append("user.gender", formData.gender);

    requestData.append("reg_no", formData.reg_no);
    requestData.append("session_admitted", formData.session_admitted || "");
    requestData.append("admission_date", formData.admission_date || "");
    requestData.append("date_of_birth", formData.date_of_birth || "");
    // requestData.append("student_class", formData?.student_class || "");

    // if (
    //   formData?.image &&
    //   formData?.image?.length > 0 &&
    //   formData?.image?.type?.startsWith("image/")
    // ) {
    //   requestData.append("user.image", formData.image);
    // } else if (formData?.image) {
    //   console.log("Please upload a valid image file.");
    // }

    try {
      const url = type === "create" ? "/students/" : `/students/${data.id}/`;

      const func = type === "create" ? apiPost : apiPut;

      const response = await func(url, requestData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (!response.success || !response?.data) {
        throw response;
      }

      console.log("Success:", response);
      toast.success(
        `Student ${type === "create" ? "created" : "updated"} successfully!`
      );

      if (successFunction) {
        successFunction();
      }
    } catch (error: any) {
      console.log("Error: ==", error);
      console.log(error.response);

      if (error?.response) {
        if (error?.response?.status == 500) {
          return toast.error("Server Error, please try gain later");
        }
        // Server responded with a status other than 200 range
        const errorMessage = error.response.data;
        if (typeof errorMessage === "object") {
          Object.values(errorMessage).forEach((msgArray: any) => {
            try {
              let msgs;
              console.log(typeof msgArray, Object.values(msgArray));
              console.log(Object.keys(msgArray));

              if (Array.isArray(msgArray)) {
                msgArray.forEach((msg: string) => {
                  console.log(msg, "array");
                  toast.error(msg?.replace(/^\['|'\]$/g, ""));
                });
              } else if (typeof msgArray === "string") {
                msgs = msgArray?.replace(/^\['|'\]$/g, "");
                toast.error(msgs);
              } else if (typeof msgArray === "object") {
                Object.values(msgArray).forEach((msg: any) => {
                  console.log("msg object", msg);

                  if (Array.isArray(msg)) {
                    msg.forEach((ms: string) => {
                      console.log(ms, "array");
                      toast.error(ms?.replace(/^\['|'\]$/g, ""));
                    });
                  } else {
                    toast.error(msg?.replace(/^\['|'\]$/g, ""));
                  }
                });
              } else {
                console.warn("Unexpected error format found:", msgs, msgArray);
                toast.error("Error: " + msgArray);
              }
            } catch (error) {
              console.warn("Error parsing error message:", error);
              toast.error(
                "An error occurred while processing the error message."
              );
            }
          });
        } else {
          toast.error(errorMessage);
        }
      } else if (error.message && error.message.includes("Network Error")) {
        // Network error occurred
        console.error("Network error:", error.message);
        toast.error("Network error. Please check your internet connection.");
      } else if (error.request) {
        // Request was made but no response received
        console.error("Error request:", error.request);
        toast.error("No response from server. Please try again later.");
      } else {
        // Something else happened while setting up the request
        console.error("Error message:", error.message);

        toast.error(
          `Failed to ${
            type === "create" ? "create" : "update"
          } teacher,  Please try again.`
        );
      }
    }
  });

  const fetchClassess = async () => {
    try {
      const url = `/classes/all/`;

      const response = await apiGet(url);
      console.log(url);
      console.log(response.data);

      setClasses(response.data);
    } catch (error: any) {
      console.warn("Error fetching classes:", error);
      console.warn("Error fetching classes:", error?.response);
    } finally {
      // setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClassess();
  }, []);

  return (
    <form className="flex flex-col gap-8" method="post" onSubmit={onSubmit}>
      <h1 className="text-xl font-semibold">
        {type === "create" ? "Create a new student" : "Update student"}
      </h1>
      <span className="text-xs text-gray-400 font-medium">
        Authentication Information
      </span>
      <div className="flex justify-between flex-wrap gap-4">
        {/* <InputField
          label="Username"
          name="username"
          defaultValue={data?.username}
          register={register}
          error={errors?.username}
        /> */}
        <InputField
          label="Email"
          name="email"
          defaultValue={data?.email}
          register={register}
          error={errors?.email}
        />
        {type === "create" && (
          <InputField
            label="Password"
            name="password"
            defaultValue={"Last Name In lower case"} // Default password for new students
            register={register}
            error={errors?.password}
            disabled
          />
        )}
      </div>
      <span className="text-xs text-gray-400 font-medium">
        Personal Information
      </span>
      <div className="flex justify-between flex-wrap gap-4">
        <InputField
          label="First Name"
          name="firstName"
          defaultValue={data?.firstName}
          register={register}
          error={errors.firstName}
        />
        <InputField
          label="Last Name"
          name="lastName"
          defaultValue={data?.lastName}
          register={register}
          error={errors.lastName}
        />
        {/* <InputField
          label="Phone"
          name="phone"
          defaultValue={data?.phone}
          register={register}
          error={errors.phone}
        />
        <InputField
          label="Department"
          name="department"
          defaultValue={data?.department}
          register={register}
          error={errors.department}
        /> */}
        <div className="flex flex-col gap-2 w-full md:w-1/4">
          <label className="text-xs text-gray-500">Gender</label>
          <select
            className="ring-[1.5px] ring-gray-300 p-2 rounded-md text-sm w-full"
            {...register("gender")}
            defaultValue={data?.gender}
          >
            <option value="M">Male</option>
            <option value="F">Female</option>
          </select>
          {errors.gender?.message && (
            <p className="text-xs text-red-400">
              {errors.gender?.message.toString()}
            </p>
          )}
        </div>
        <div className="flex flex-col gap-2 w-full md:w-1/4 justify-center">
          <label
            className="text-xs text-gray-500 flex items-center gap-2 cursor-pointer"
            htmlFor="img"
          >
            <Image src="/upload.png" alt="" width={28} height={28} />
            <span>Upload a photo</span>
          </label>
          <input
            type="file"
            id="img"
            {...register("image")}
            className="hidden"
            onChange={handleImageChange}
          />
          {errors.image?.message && (
            <p className="text-xs text-red-400">
              {errors.image?.message.toString()}
            </p>
          )}
        </div>
      </div>
      <span className="text-xs text-gray-400 font-medium">
        Student Information
      </span>
      <div className="flex justify-between flex-wrap gap-4">
        <InputField
          label="Registration Number"
          name="reg_no"
          defaultValue={data?.reg_no}
          register={register}
          error={errors?.reg_no}
        />
        <InputField
          label="Session Admitted"
          name="session_admitted"
          defaultValue={data?.session_admitted}
          register={register}
          error={errors?.session_admitted}
        />
        <InputField
          label="Admission Date"
          name="admission_date"
          type="date"
          defaultValue={data?.admission_date}
          register={register}
          error={errors?.admission_date}
        />
        <InputField
          label="Date of Birth"
          name="date_of_birth"
          type="date"
          defaultValue={data?.date_of_birth}
          register={register}
          error={errors?.date_of_birth}
        />
        {/* <div className="flex flex-col gap-2 w-full md:w-1/4">
          <label className="text-xs text-gray-500">Student Class</label>
          <select
            className="ring-[1.5px] ring-gray-300 p-2 rounded-md text-sm w-full"
            {...register("student_class")}
            defaultValue={data?.student_class || ""}
          >
            <option value="" disabled>
              Select a class
            </option>
            {classes.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.name_display}
              </option>
            ))}
          </select>
          {errors?.student_class?.message && (
            <p className="text-xs text-red-400">
              {errors.student_class.message.toString()}
            </p>
          )}
        </div> */}
      </div>
      <div className="flex justify-center">
        {imagePreview ? (
          <img
            id="preview-image"
            className="mt-2 mx-auto w-24 h-24 object-cover rounded-full border-2"
            alt="Selected Image Preview"
            src={imagePreview || "/avatar-placeholder.png"}
          />
        ) : (
          <CircleUserRound size={96} />
        )}
      </div>
      <button className="bg-blue-400 text-white p-2 rounded-md">
        {type === "create" ? "Create" : "Update"}
      </button>
    </form>
  );
};

export default StudentForm;
