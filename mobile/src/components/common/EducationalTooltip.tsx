import React, { useState } from 'react';
import {
View,
Text,
TouchableOpacity,
StyleSheet,
Animated,
Dimensions,
Modal,
TouchableWithoutFeedback,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
const { width: screenWidth } = Dimensions.get('window');
interface EducationalTooltipProps {
term: string;
explanation: string;
children: React.ReactNode;
position?: 'top' | 'bottom' | 'left' | 'right';
maxWidth?: number;
style?: any;
hideExternalIcon?: boolean;
}
const EducationalTooltip: React.FC<EducationalTooltipProps> = ({
term,
explanation,
children,
position = 'top',
maxWidth = 280,
style,
hideExternalIcon = false,
}) => {
const [showTooltip, setShowTooltip] = useState(false);
const [tooltipAnimation] = useState(new Animated.Value(0));
const showTooltipWithAnimation = () => {
setShowTooltip(true);
Animated.spring(tooltipAnimation, {
toValue: 1,
useNativeDriver: true,
tension: 100,
friction: 8,
}).start();
};
const hideTooltipWithAnimation = () => {
Animated.timing(tooltipAnimation, {
toValue: 0,
duration: 200,
useNativeDriver: true,
}).start(() => {
setShowTooltip(false);
});
};
return (
<View style={[styles.container, style]}>
<TouchableOpacity
onPress={showTooltipWithAnimation}
onLongPress={showTooltipWithAnimation}
activeOpacity={0.7}
style={styles.touchableContent}
>
{children}
</TouchableOpacity>
{!hideExternalIcon && (
<TouchableOpacity
onPress={showTooltipWithAnimation}
onLongPress={showTooltipWithAnimation}
activeOpacity={0.7}
style={styles.infoIcon}
>
<Icon name="info" size={12} color="#007AFF" />
</TouchableOpacity>
)}
<Modal
visible={showTooltip}
transparent={true}
animationType="fade"
onRequestClose={hideTooltipWithAnimation}
>
<TouchableWithoutFeedback onPress={hideTooltipWithAnimation}>
<View style={styles.modalOverlay}>
<TouchableWithoutFeedback>
<Animated.View
style={[
styles.tooltipModal,
{
opacity: tooltipAnimation,
transform: [
{
scale: tooltipAnimation.interpolate({
inputRange: [0, 1],
outputRange: [0.8, 1],
}),
},
],
},
]}
>
<View style={styles.tooltipHeader}>
<Text style={styles.tooltipTerm}>{term}</Text>
<TouchableOpacity
onPress={hideTooltipWithAnimation}
style={styles.closeButton}
>
<Icon name="x" size={16} color="#8E8E93" />
</TouchableOpacity>
</View>
<Text style={styles.tooltipExplanation}>{explanation}</Text>
</Animated.View>
</TouchableWithoutFeedback>
</View>
</TouchableWithoutFeedback>
</Modal>
</View>
);
};
const styles = StyleSheet.create({
container: {
position: 'relative',
},
touchableContent: {
width: '100%',
},
infoIcon: {
position: 'absolute',
top: 0,
right: -16,
padding: 2,
zIndex: 1,
},
modalOverlay: {
flex: 1,
backgroundColor: 'rgba(0, 0, 0, 0.5)',
justifyContent: 'center',
alignItems: 'center',
padding: 20,
},
tooltipModal: {
backgroundColor: '#1C1C1E',
borderRadius: 12,
padding: 16,
maxWidth: 320,
width: '100%',
shadowColor: '#000',
shadowOffset: { width: 0, height: 4 },
shadowOpacity: 0.3,
shadowRadius: 8,
elevation: 20,
},
tooltipHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 12,
},
tooltipTerm: {
fontSize: 16,
fontWeight: '600',
color: '#FFFFFF',
flex: 1,
},
closeButton: {
padding: 4,
},
tooltipExplanation: {
fontSize: 14,
lineHeight: 20,
color: '#E5E5EA',
},
});
export default EducationalTooltip;
