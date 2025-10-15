import * as React from 'react';
import { TextInput, TextInputProps } from 'react-native';

type Props = {
  value?: number | string;
  onSubmitValue?: (n: number | null) => void;
} & Omit<TextInputProps, 'value' | 'onChangeText' | 'onSubmitEditing'>;

export const StableNumberInput = ({ value, onSubmitValue, ...rest }: Props) => {
  // keep a local string so parent re-renders don't stomp focus
  const [text, setText] = React.useState(
    value === 0 || value ? String(value) : ''
  );
  const ref = React.useRef<TextInput>(null);

  // if parent changes the value externally, only update when different
  React.useEffect(() => {
    const v = value === 0 || value ? String(value) : '';
    if (v !== text) setText(v);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  const commit = React.useCallback(() => {
    const n = text.trim() ? Number(text) : null;
    onSubmitValue?.(Number.isFinite(n as number) ? (n as number) : null);
  }, [text, onSubmitValue]);

  return (
    <TextInput
      ref={ref}
      value={text}
      onChangeText={(t) => {
        // allow only digits, don't format while typing
        const cleaned = t.replace(/\D+/g, '').slice(0, 3); // age up to 3 digits
        setText(cleaned);
      }}
      onSubmitEditing={commit}
      onBlur={commit}
      blurOnSubmit={false}                // <- keep focus on Return unless you blur manually
      keyboardType="number-pad"
      inputMode="numeric"
      autoCorrect={false}
      autoCapitalize="none"
      {...rest}
    />
  );
};
