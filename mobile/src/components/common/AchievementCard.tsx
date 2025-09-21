import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface AchievementCardProps {
achievement: {
id: string;
title: string;
description: string;
icon: string;
earned_at: string;
user: {
name: string;
profile_pic?: string;
};
};
onPress: () => void;
}
const AchievementCard: React.FC<AchievementCardProps> = ({
achievement,
onPress,
}) => {
const formatDate = (dateString: string) => {
const date = new Date(dateString);
const now = new Date();
const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
if (diffInDays === 0) return 'Today';
if (diffInDays === 1) return 'Yesterday';
if (diffInDays < 7) return `${diffInDays} days ago`;
return date.toLocaleDateString();
};
return (
<TouchableOpacity style={styles.container} onPress={onPress}>
{/* Achievement Icon */}
<View style={styles.iconContainer}>
<Text style={styles.achievementIcon}>{achievement.icon}</Text>
</View>
{/* Content */}
<View style={styles.content}>
<Text style={styles.title}>{achievement.title}</Text>
<Text style={styles.description}>{achievement.description}</Text>
<View style={styles.userInfo}>
{achievement.user.profile_pic ? (
<Image
source={{ uri: achievement.user.profile_pic }}
style={styles.avatar}
/>
) : (
<View style={styles.avatarFallback}>
<Text style={styles.avatarText}>
{achievement.user.name.charAt(0).toUpperCase()}
</Text>
</View>
)}
<View style={styles.userDetails}>
<Text style={styles.userName}>{achievement.user.name}</Text>
<Text style={styles.timestamp}>{formatDate(achievement.earned_at)}</Text>
</View>
</View>
</View>
{/* Achievement Badge */}
<View style={styles.badgeContainer}>
<Icon name="award" size={20} color="#FFD700" />
</View>
</TouchableOpacity>
);
};
const styles = StyleSheet.create({
container: {
backgroundColor: '#FFFFFF',
borderRadius: 16,
padding: 16,
marginHorizontal: 16,
marginVertical: 8,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 3,
flexDirection: 'row',
alignItems: 'center',
},
iconContainer: {
width: 60,
height: 60,
borderRadius: 30,
backgroundColor: '#FFF8E1',
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
borderWidth: 2,
borderColor: '#FFD700',
},
achievementIcon: {
fontSize: 28,
},
content: {
flex: 1,
},
title: {
fontSize: 18,
fontWeight: '700',
color: '#1C1C1E',
marginBottom: 6,
},
description: {
fontSize: 14,
color: '#3A3A3C',
lineHeight: 20,
marginBottom: 12,
},
userInfo: {
flexDirection: 'row',
alignItems: 'center',
},
avatar: {
width: 24,
height: 24,
borderRadius: 12,
marginRight: 8,
},
avatarFallback: {
width: 24,
height: 24,
borderRadius: 12,
marginRight: 8,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
},
avatarText: {
color: '#FFFFFF',
fontSize: 10,
fontWeight: '600',
},
userDetails: {
flex: 1,
},
userName: {
fontSize: 12,
fontWeight: '600',
color: '#007AFF',
marginBottom: 2,
},
timestamp: {
fontSize: 10,
color: '#8E8E93',
},
badgeContainer: {
width: 40,
height: 40,
borderRadius: 20,
backgroundColor: '#FFF8E1',
justifyContent: 'center',
alignItems: 'center',
marginLeft: 12,
},
});
export default AchievementCard;
