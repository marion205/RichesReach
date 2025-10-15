import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface Props {
children: ReactNode;
fallback?: ReactNode;
onError?: (error: Error, errorInfo: ErrorInfo) => void;
}
interface State {
hasError: boolean;
error: Error | null;
errorInfo: ErrorInfo | null;
}
class ErrorBoundary extends Component<Props, State> {
constructor(props: Props) {
super(props);
this.state = {
hasError: false,
error: null,
errorInfo: null,
};
}
static getDerivedStateFromError(error: Error): State {
// Update state so the next render will show the fallback UI
return {
hasError: true,
error,
errorInfo: null,
};
}
componentDidCatch(error: Error, errorInfo: ErrorInfo) {
// Log error to console and any error reporting service
console.error('ErrorBoundary caught an error:', error, errorInfo);
this.setState({
error,
errorInfo,
});
// Call custom error handler if provided
if (this.props.onError) {
this.props.onError(error, errorInfo);
}
// Here you could send error to crash reporting service
// Example: crashlytics().recordError(error);
}
handleRetry = () => {
this.setState({
hasError: false,
error: null,
errorInfo: null,
});
};
render() {
if (this.state.hasError) {
// Custom fallback UI
if (this.props.fallback) {
return this.props.fallback;
}
// Default error UI
return (
<View style={styles.container}>
<ScrollView contentContainerStyle={styles.scrollContent}>
<View style={styles.errorContainer}>
<Icon name="alert-triangle" size={64} color="#FF3B30" />
<Text style={styles.title}>Something went wrong</Text>
<Text style={styles.message}>
We're sorry, but something unexpected happened. Please try again.
</Text>
<TouchableOpacity style={styles.retryButton} onPress={this.handleRetry}>
<Icon name="refresh-cw" size={20} color="#FFFFFF" />
<Text style={styles.retryButtonText}>Try Again</Text>
</TouchableOpacity>
{__DEV__ && this.state.error && (
<View style={styles.debugContainer}>
<Text style={styles.debugTitle}>Debug Information:</Text>
<Text style={styles.debugText}>
{this.state.error.toString()}
</Text>
{this.state.errorInfo && (
<Text style={styles.debugText}>
{this.state.errorInfo.componentStack}
</Text>
)}
</View>
)}
</View>
</ScrollView>
</View>
);
}
return this.props.children;
}
}
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
scrollContent: {
flexGrow: 1,
justifyContent: 'center',
padding: 20,
},
errorContainer: {
alignItems: 'center',
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 24,
shadowColor: '#000',
shadowOffset: {
width: 0,
height: 2,
},
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
title: {
fontSize: 24,
fontWeight: '700',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
textAlign: 'center',
},
message: {
fontSize: 16,
color: '#6C757D',
textAlign: 'center',
lineHeight: 24,
marginBottom: 24,
},
retryButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#007AFF',
paddingHorizontal: 24,
paddingVertical: 12,
borderRadius: 8,
marginBottom: 16,
},
retryButtonText: {
color: '#FFFFFF',
fontSize: 16,
fontWeight: '600',
marginLeft: 8,
},
debugContainer: {
width: '100%',
backgroundColor: '#F8F9FA',
borderRadius: 8,
padding: 16,
marginTop: 16,
},
debugTitle: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 8,
},
debugText: {
fontSize: 12,
color: '#6C757D',
fontFamily: 'monospace',
lineHeight: 16,
},
});
export default ErrorBoundary;
