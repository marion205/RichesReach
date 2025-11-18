/**
 * Validation Utilities
 * 
 * Provides real-time validation functions with clear error messages
 * for forms across the app.
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

export interface FieldValidation {
  validate: (value: any, context?: any) => ValidationResult;
  errorMessage?: string;
}

/**
 * Validate symbol (stock ticker)
 */
export const validateSymbol = (symbol: string): ValidationResult => {
  if (!symbol || symbol.trim().length === 0) {
    return {
      isValid: false,
      error: 'Symbol is required',
    };
  }

  const trimmed = symbol.trim().toUpperCase();
  
  // Basic format validation (1-5 letters, optional numbers)
  if (!/^[A-Z]{1,5}(\d+)?$/.test(trimmed)) {
    return {
      isValid: false,
      error: 'Invalid symbol format. Use 1-5 letters (e.g., AAPL, MSFT)',
    };
  }

  if (trimmed.length > 5) {
    return {
      isValid: false,
      error: 'Symbol must be 5 characters or less',
    };
  }

  return { isValid: true };
};

/**
 * Validate quantity
 */
export const validateQuantity = (
  quantity: string,
  min: number = 1,
  max: number = 1000000
): ValidationResult => {
  if (!quantity || quantity.trim().length === 0) {
    return {
      isValid: false,
      error: 'Quantity is required',
    };
  }

  const num = parseFloat(quantity);
  
  if (isNaN(num)) {
    return {
      isValid: false,
      error: 'Quantity must be a number',
    };
  }

  if (num <= 0) {
    return {
      isValid: false,
      error: 'Quantity must be greater than 0',
    };
  }

  if (num < min) {
    return {
      isValid: false,
      error: `Quantity must be at least ${min}`,
    };
  }

  if (num > max) {
    return {
      isValid: false,
      error: `Quantity cannot exceed ${max.toLocaleString()}`,
    };
  }

  if (!Number.isInteger(num)) {
    return {
      isValid: false,
      error: 'Quantity must be a whole number',
    };
  }

  return { isValid: true };
};

/**
 * Validate price
 */
export const validatePrice = (
  price: string,
  min: number = 0.01,
  max: number = 1000000
): ValidationResult => {
  if (!price || price.trim().length === 0) {
    return {
      isValid: false,
      error: 'Price is required',
    };
  }

  const num = parseFloat(price);
  
  if (isNaN(num)) {
    return {
      isValid: false,
      error: 'Price must be a number',
    };
  }

  if (num <= 0) {
    return {
      isValid: false,
      error: 'Price must be greater than 0',
    };
  }

  if (num < min) {
    return {
      isValid: false,
      error: `Price must be at least $${min.toFixed(2)}`,
    };
  }

  if (num > max) {
    return {
      isValid: false,
      error: `Price cannot exceed $${max.toLocaleString()}`,
    };
  }

  // Check decimal places (max 2 for currency)
  const decimalPlaces = (price.split('.')[1] || '').length;
  if (decimalPlaces > 2) {
    return {
      isValid: false,
      error: 'Price can have at most 2 decimal places',
    };
  }

  return { isValid: true };
};

/**
 * Validate stop price (must be different from current price)
 */
export const validateStopPrice = (
  stopPrice: string,
  currentPrice?: number,
  orderSide: 'buy' | 'sell' = 'buy'
): ValidationResult => {
  const priceValidation = validatePrice(stopPrice);
  if (!priceValidation.isValid) {
    return priceValidation;
  }

  if (currentPrice !== undefined) {
    const stop = parseFloat(stopPrice);
    const diff = Math.abs(stop - currentPrice);
    const percentDiff = (diff / currentPrice) * 100;

    // Stop price should be at least 1% away from current price
    if (percentDiff < 1) {
      return {
        isValid: false,
        error: 'Stop price must be at least 1% away from current price',
      };
    }

    // For buy stops, stop should be above current price
    if (orderSide === 'buy' && stop <= currentPrice) {
      return {
        isValid: false,
        error: 'Buy stop price must be above current price',
      };
    }

    // For sell stops, stop should be below current price
    if (orderSide === 'sell' && stop >= currentPrice) {
      return {
        isValid: false,
        error: 'Sell stop price must be below current price',
      };
    }
  }

  return { isValid: true };
};

/**
 * Validate limit price against current market price
 */
export const validateLimitPrice = (
  limitPrice: string,
  currentPrice?: number,
  orderSide: 'buy' | 'sell' = 'buy'
): ValidationResult => {
  const priceValidation = validatePrice(limitPrice);
  if (!priceValidation.isValid) {
    return priceValidation;
  }

  if (currentPrice !== undefined) {
    const limit = parseFloat(limitPrice);
    
    // For buy limits, limit should be at or below current price
    if (orderSide === 'buy' && limit > currentPrice * 1.05) {
      return {
        isValid: false,
        error: 'Buy limit price should not exceed current price by more than 5%',
      };
    }

    // For sell limits, limit should be at or above current price
    if (orderSide === 'sell' && limit < currentPrice * 0.95) {
      return {
        isValid: false,
        error: 'Sell limit price should not be below current price by more than 5%',
      };
    }
  }

  return { isValid: true };
};

/**
 * Validate order total (quantity * price)
 */
export const validateOrderTotal = (
  quantity: string,
  price: string,
  maxTotal?: number
): ValidationResult => {
  const qtyValidation = validateQuantity(quantity);
  if (!qtyValidation.isValid) {
    return qtyValidation;
  }

  const priceValidation = validatePrice(price);
  if (!priceValidation.isValid) {
    return priceValidation;
  }

  const qty = parseFloat(quantity);
  const priceNum = parseFloat(price);
  const total = qty * priceNum;

  if (maxTotal && total > maxTotal) {
    return {
      isValid: false,
      error: `Order total ($${total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}) exceeds maximum of $${maxTotal.toLocaleString()}`,
    };
  }

  return { isValid: true };
};

/**
 * Real-time validation hook helper
 */
export const createValidator = <T>(
  validations: Record<keyof T, FieldValidation>
) => {
  return (field: keyof T, value: any, context?: any): ValidationResult => {
    const validation = validations[field];
    if (!validation) {
      return { isValid: true };
    }

    return validation.validate(value, context);
  };
};

/**
 * Validate entire form
 */
export const validateForm = <T extends Record<string, any>>(
  formData: T,
  validations: Record<keyof T, FieldValidation>
): { isValid: boolean; errors: Record<keyof T, string | undefined> } => {
  const errors: Record<keyof T, string | undefined> = {} as any;
  let isValid = true;

  for (const field in validations) {
    const validation = validations[field];
    const result = validation.validate(formData[field], formData);
    
    if (!result.isValid) {
      isValid = false;
      errors[field] = result.error || validation.errorMessage || 'Invalid value';
    } else {
      errors[field] = undefined;
    }
  }

  return { isValid, errors };
};

