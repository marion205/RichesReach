/**
 * Safe date formatting utilities to prevent "Date value out of bounds" errors
 */

/**
 * Safely formats a date string to a locale date string
 * @param dateString - The date string to format
 * @param fallback - Fallback text if date is invalid (default: 'N/A')
 * @returns Formatted date string or fallback
 */
export const safeFormatDate = (dateString: string | null | undefined, fallback: string = 'N/A'): string => {
  if (!dateString) return fallback;
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return fallback;
    }
    return date.toLocaleDateString();
  } catch (error) {
    console.warn('Date formatting error:', error, 'dateString:', dateString);
    return fallback;
  }
};

/**
 * Safely formats a date string to a locale date and time string
 * @param dateString - The date string to format
 * @param fallback - Fallback text if date is invalid (default: 'N/A')
 * @returns Formatted date and time string or fallback
 */
export const safeFormatDateTime = (dateString: string | null | undefined, fallback: string = 'N/A'): string => {
  if (!dateString) return fallback;
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return fallback;
    }
    return date.toLocaleString();
  } catch (error) {
    console.warn('Date formatting error:', error, 'dateString:', dateString);
    return fallback;
  }
};

/**
 * Safely formats a date string to a time string
 * @param dateString - The date string to format
 * @param fallback - Fallback text if date is invalid (default: 'N/A')
 * @returns Formatted time string or fallback
 */
export const safeFormatTime = (dateString: string | null | undefined, fallback: string = 'N/A'): string => {
  if (!dateString) return fallback;
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return fallback;
    }
    return date.toLocaleTimeString();
  } catch (error) {
    console.warn('Date formatting error:', error, 'dateString:', dateString);
    return fallback;
  }
};

/**
 * Safely gets the timestamp from a date string
 * @param dateString - The date string to convert
 * @param fallback - Fallback timestamp if date is invalid (default: 0)
 * @returns Timestamp or fallback
 */
export const safeGetTimestamp = (dateString: string | null | undefined, fallback: number = 0): number => {
  if (!dateString) return fallback;
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return fallback;
    }
    return date.getTime();
  } catch (error) {
    console.warn('Date conversion error:', error, 'dateString:', dateString);
    return fallback;
  }
};

/**
 * Safely creates a Date object from a date string
 * @param dateString - The date string to convert
 * @param fallback - Fallback date if conversion fails (default: new Date())
 * @returns Date object or fallback
 */
export const safeCreateDate = (dateString: string | null | undefined, fallback: Date = new Date()): Date => {
  if (!dateString) return fallback;
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return fallback;
    }
    return date;
  } catch (error) {
    console.warn('Date creation error:', error, 'dateString:', dateString);
    return fallback;
  }
};

/**
 * Checks if a date string is valid
 * @param dateString - The date string to validate
 * @returns True if the date string is valid, false otherwise
 */
export const isValidDateString = (dateString: string | null | undefined): boolean => {
  if (!dateString) return false;
  
  try {
    const date = new Date(dateString);
    return !isNaN(date.getTime());
  } catch (error) {
    return false;
  }
};
