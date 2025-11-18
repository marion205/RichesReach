import { useState, useCallback, useMemo } from 'react';
import { Alert } from 'react-native';

export type OrderType = 'market' | 'limit' | 'stop_loss';
export type OrderSide = 'buy' | 'sell';

export interface OrderFormState {
  orderType: OrderType;
  orderSide: OrderSide;
  symbol: string;
  quantity: string;
  price: string;
  stopPrice: string;
  notes: string;
}

export interface OrderFormActions {
  setOrderType: (type: OrderType) => void;
  setOrderSide: (side: OrderSide) => void;
  setSymbol: (symbol: string) => void;
  setQuantity: (quantity: string) => void;
  setPrice: (price: string) => void;
  setStopPrice: (stopPrice: string) => void;
  setNotes: (notes: string) => void;
  reset: () => void;
  validate: () => string | null;
}

const sanitizeInt = (s: string) => {
  const n = parseInt(String(s).replace(/[^\d]/g, ''), 10);
  return Number.isFinite(n) ? n : NaN;
};

const sanitizeFloat = (s: string) => {
  const n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
  return Number.isFinite(n) ? n : NaN;
};

const upper = (s: string) => String(s).trim().toUpperCase();

export const useOrderForm = (): OrderFormState & OrderFormActions => {
  const [orderType, setOrderType] = useState<OrderType>('market');
  const [orderSide, setOrderSide] = useState<OrderSide>('buy');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [notes, setNotes] = useState('');

  const reset = useCallback(() => {
    setSymbol('');
    setQuantity('');
    setPrice('');
    setStopPrice('');
    setNotes('');
    setOrderType('market');
    setOrderSide('buy');
  }, []);

  const validate = useCallback((): string | null => {
    const sym = upper(symbol);
    const qty = sanitizeInt(quantity);
    
    if (!sym) return 'Please enter a symbol';
    if (!qty || qty <= 0) return 'Quantity must be a positive integer';
    
    if (orderType === 'limit') {
      const p = sanitizeFloat(price);
      if (!Number.isFinite(p) || p <= 0) return 'Enter a valid limit price';
    }
    
    if (orderType === 'stop_loss') {
      const sp = sanitizeFloat(stopPrice);
      if (!Number.isFinite(sp) || sp <= 0) return 'Enter a valid stop price';
    }
    
    return null;
  }, [symbol, quantity, orderType, price, stopPrice]);

  return {
    orderType,
    orderSide,
    symbol,
    quantity,
    price,
    stopPrice,
    notes,
    setOrderType,
    setOrderSide,
    setSymbol: useCallback((s: string) => setSymbol(upper(s)), []),
    setQuantity,
    setPrice,
    setStopPrice,
    setNotes,
    reset,
    validate,
  };
};

