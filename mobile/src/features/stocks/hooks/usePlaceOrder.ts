import { useState } from 'react';
import { useMutation } from '@apollo/client';
import { Alert } from 'react-native';
import { PLACE_STOCK_ORDER } from '../../../graphql/tradingQueries';
import { alpacaAnalytics } from '../../../services/alpacaAnalyticsService';
import { OrderType, OrderSide } from './useOrderForm';

const sanitizeInt = (s: string) => {
  const n = parseInt(String(s).replace(/[^\d]/g, ''), 10);
  return Number.isFinite(n) ? n : NaN;
};

const sanitizeFloat = (s: string) => {
  const n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
  return Number.isFinite(n) ? n : NaN;
};

const upper = (s: string) => String(s).trim().toUpperCase();

interface PlaceOrderParams {
  symbol: string;
  quantity: string;
  orderType: OrderType;
  orderSide: OrderSide;
  price?: string;
  stopPrice?: string;
  alpacaAccount?: any;
  onConnectRequired?: () => void;
  onSuccess?: () => void;
  refetchQueries?: Array<() => Promise<any>>;
}

export const usePlaceOrder = () => {
  const [placeStockOrder] = useMutation(PLACE_STOCK_ORDER, { errorPolicy: 'all' });
  const [isPlacing, setIsPlacing] = useState(false);

  const placeOrder = async ({
    symbol,
    quantity,
    orderType,
    orderSide,
    price,
    stopPrice,
    alpacaAccount,
    onConnectRequired,
    onSuccess,
    refetchQueries = [],
  }: PlaceOrderParams) => {
    setIsPlacing(true);
    try {
      const sym = upper(symbol);
      const qty = sanitizeInt(quantity);

      // Check if user has Alpaca account
      if (!alpacaAccount) {
        alpacaAnalytics.track('connect_initiated', { source: 'order_placement' });
        setIsPlacing(false);
        onConnectRequired?.();
        return;
      }

      // Check if account is approved for trading
      if (!alpacaAccount.approvedAt) {
        Alert.alert(
          'Account Not Approved',
          'Your Alpaca account is not yet approved for trading. Please complete the KYC process first.',
          [{ text: 'OK' }]
        );
        setIsPlacing(false);
        return;
      }

      // Prepare order variables
      const orderVariables: OrderVariables = {
        symbol: sym,
        side: orderSide.toUpperCase() as 'BUY' | 'SELL',
        quantity: qty,
        orderType:
          orderType === 'market' ? 'MARKET' : orderType === 'limit' ? 'LIMIT' : 'STOP',
        timeInForce: 'DAY',
      };

      if (orderType === 'limit' && price) {
        orderVariables.limitPrice = sanitizeFloat(price);
      }

      // Place order through Alpaca
      const res = await placeStockOrder({ variables: orderVariables });
      const orderResponse = res?.data?.placeStockOrder as PlaceOrderResponse | undefined;
      const success = orderResponse?.success;
      const message = orderResponse?.message;
      const orderId = orderResponse?.orderId;

      if (success) {
        Alert.alert('Order Placed Successfully', `${message}\n\nOrder ID: ${orderId}`, [
          { text: 'OK' },
        ]);
        onSuccess?.();

        // Refresh data
        await Promise.all(refetchQueries.map((refetch) => refetch()));
      } else {
        Alert.alert('Order Failed', message || 'Could not place order. Please try again.');
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Could not place order. Please try again.';
      logger.error('Order placement failed:', e);
      Alert.alert('Order Failed', errorMessage);
    } finally {
      setIsPlacing(false);
    }
  };

  return {
    placeOrder,
    isPlacing,
  };
};

