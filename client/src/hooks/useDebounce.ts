import { useState, useEffect } from "react";

/**
 * A custom React hook that returns a debounced value after a specified delay.
 * This is useful for delaying the execution of functions like search inputs or other
 * operations that don't need to happen on every keystroke.
 *
 * @template T - The type of the value being debounced
 * @param {T} value - The value to debounce
 * @param {number} [delay=500] - The delay in milliseconds before updating the debounced value
 * @returns {T} The debounced value
 *
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 *
 * useEffect(() => {
 *   if (debouncedSearchTerm) {
 *     // Perform search API call
 *     searchAPI(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 */
function useDebounce<T>(value: T, delay: number = 500): T {
  // State to store the debounced value
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up a timer to update the debounced value after the specified delay
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timer if the value or delay changes (or on unmount)
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;
