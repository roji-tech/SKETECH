export interface UserType {
  id?: string;
  fullName?: string | null | undefined;
  firstName?: string | null | undefined;
  lastName?: string | null | undefined;
  image?: string | null | undefined;
  role?: string;
  username?: string;
  accessToken?: string;
  email?: string;
  gender?: string;
  phone?: string;
  address?: string;
  accessTokenExpires?: number;
  schoolLogo?: string;
  schoolName?: string;
  schoolShortName?: string;
  schoolCode?: string;
  isOwner?: boolean;
  error?: string;

  // refreshTOken?: string;
}

// Interface for expected request body structure
export interface RegisterRequestBody {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  gender: string;
  school_name: string;
  school_phone: string;
  school_email: string;
}

// Interface for the decoded JWT token
export interface DecodedToken {
  exp: number; // Expiry timestamp
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  image: string;
  gender: string;
  phone: string;
  role: string;
  // is_superuser: boolean;
  // is_staff: boolean;
}

export type MyFormProps = {
  type: "create" | "update" | "delete" | "view";
  data?: any;
  onSuccess?: Function | null | undefined;
};
