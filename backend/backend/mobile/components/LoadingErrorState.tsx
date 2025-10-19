import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface LoadingErrorStateProps {
loading?: boolean;
error?: string | null;
onRetry?: () => void;
emptyMessage?: string;
showEmpty?: boolean;
style?: any;
}
const LoadingErrorState: React.FC<LoadingErrorStateProps> = ({
loading = false,
error = null,
onRetry,
emptyMessage = 'No data available',
showEmpty = false,
style,
}) => {
if (loading) {
return (
<View style={[styles.container, style]}>
<ActivityIndicator size="large" color="#007AFF" />
<Text style={styles.loadingText}>Loading...</Text>
</View>
);
}
if (error) {
return (
<View style={[styles.container, style]}>
<Icon name="alert-circle" size={48} color="#FF3B30" />
<Text style={styles.errorTitle}>Something went wrong</Text>
<Text style={styles.errorMessage}>{error}</Text>
{onRetry && (
<TouchableOpacity style={styles.retryButton} onPress={onRetry}>
<Icon name="refresh-cw" size={20} color="#FFFFFF" />
<Text style={styles.retryButtonText}>Try Again</Text>
</TouchableOpacity>
)}
</View>
);
}
if (showEmpty) {
return (
<View style={[styles.container, style]}>
<Icon name="inbox" size={48} color="#8E8E93" />
<Text style={styles.emptyTitle}>No data available</Text>
<Text style={styles.emptyMessage}>{emptyMessage}</Text>
</View>
);
}
return null;
};
const styles = StyleSheet.create({
container: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 20,
backgroundColor: '#F2F2F7',
},
loadingText: {
fontSize: 16,
color: '#6C757D',
marginTop: 16,
fontWeight: '500',
},
errorTitle: {
fontSize: 20,
fontWeight: '700',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
textAlign: 'center',
},
errorMessage: {
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
},
retryButtonText: {
color: '#FFFFFF',
fontSize: 16,
fontWeight: '600',
marginLeft: 8,
},
emptyTitle: {
fontSize: 20,
fontWeight: '700',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
textAlign: 'center',
},
emptyMessage: {
fontSize: 16,
color: '#6C757D',
textAlign: 'center',
lineHeight: 24,
},
});
export default LoadingErrorState;
