/**
 * Formats a phone number into a more readable format
 * @param phoneNumber - The phone number to format (can include non-numeric characters)
 * @returns Formatted phone number string (e.g., (123) 456-7890)
 */
export const formatPhoneNumber = (phoneNumber?: string | null): string => {
  if (!phoneNumber) return "";

  // Remove all non-digit characters
  const cleaned = phoneNumber.replace(/\D/g, "");

  // Check if the phone number is empty after cleaning
  if (!cleaned) return "";

  // Format based on the length of the cleaned number
  const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/);

  if (match) {
    const areaCode = match[1] ? `(${match[1]}` : "";
    const firstPart = match[2] ? `) ${match[2]}` : "";
    const secondPart = match[3] ? `-${match[3]}` : "";

    // Only return the formatted string if we have at least one digit
    if (areaCode || firstPart || secondPart) {
      return `${areaCode}${firstPart}${secondPart}`.trim();
    }
  }

  // Return the original if we can't format it
  return phoneNumber;
};

/**
 * Capitalizes the first letter of a string
 * @param str - The string to capitalize
 * @returns String with first letter capitalized
 */
export const capitalizeFirstLetter = (str: string): string => {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};
