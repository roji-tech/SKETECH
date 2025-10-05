export const isAllowed = (role: any, allowedRoles: string[]) => {
  if (
    !role ||
    typeof role !== "string" ||
    !allowedRoles ||
    !Array.isArray(allowedRoles)
  )
    return false;
  return allowedRoles.includes(role);
};

export const isAdmin = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "admin" || role === "owner";
};

export const isOwner = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "owner";
};

export const isStaff = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "staff";
};

export const isStudent = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "student";
};

export const isParent = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "parent";
};

export const isTeachingStaff = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "staff";
};

export const isAdminAndTeachingStaff = (role: any) => {
  if (!role || typeof role !== "string") return false;
  return role === "admin" || role === "owner" || role === "staff";
};
