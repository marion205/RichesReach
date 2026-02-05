import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Image,
  StyleSheet,
  Dimensions,
  Alert,
  Modal,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { safeSpeak, stopAllSpeech } from '../../../hooks/useSafeSpeak';
import * as Haptics from 'expo-haptics';
import ConfettiCannon from 'react-native-confetti-cannon';
import SocialFeed from '../components/SocialFeed';
import logger from '../../../utils/logger';

const { width, height } = Dimensions.get('window');

interface MemeTemplate {
  id: string;
  name: string;
  imageUrl: string;
  culturalTheme: string;
  description: string;
}

interface MemeCoin {
  id: string;
  name: string;
  symbol: string;
  price: number;
  change: number;
  holders: number;
  marketCap: number;
  volume24h: number;
}

interface Raid {
  id: string;
  name: string;
  memeCoin: MemeCoin;
  targetAmount: number;
  currentAmount: number;
  participants: number;
  xpReward: number;
  timeLeft: string;
  isActive: boolean;
}

interface DeFiPool {
  id: string;
  name: string;
  apy: number;
  tvl: number;
  token1: string;
  token2: string;
  risk: 'low' | 'medium' | 'high';
}

const MemeQuestScreen: React.FC = () => {
  const [step, setStep] = useState(1); // 1: Create, 2: Raid, 3: DeFi
  const [memeName, setMemeName] = useState('');
  const [memeDescription, setMemeDescription] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<MemeTemplate | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [currentStreak, setCurrentStreak] = useState(7);
  const [totalXP, setTotalXP] = useState(1250);
  const [questProgress, setQuestProgress] = useState(2);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [voiceCommand, setVoiceCommand] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [pulseAnim] = useState(new Animated.Value(1));
  const [scrollY] = useState(new Animated.Value(0));
  const [userRank, setUserRank] = useState(5);
  const [showXPModal, setShowXPModal] = useState(false);
  const [showStreakModal, setShowStreakModal] = useState(false);
  const [leaderboard, setLeaderboard] = useState([
    { id: 1, username: '@CryptoKing', xp: 2500, streak: 15, avatar: '👑' },
    { id: 2, username: '@MemeMaster', xp: 2200, streak: 12, avatar: '🎭' },
    { id: 3, username: '@DeFiDiva', xp: 2000, streak: 10, avatar: '💎' },
    { id: 4, username: '@PumpPro', xp: 1800, streak: 8, avatar: '🚀' },
    { id: 5, username: '@You', xp: 1250, streak: 7, avatar: '🔥' },
  ]);
  const [dailyChallenges, setDailyChallenges] = useState([
    { id: 1, title: 'Launch 3 Memes', progress: 2, total: 3, reward: 100, completed: false },
    { id: 2, title: 'Join 5 Raids', progress: 3, total: 5, reward: 150, completed: false },
    { id: 3, title: 'Stake in DeFi Pool', progress: 0, total: 1, reward: 200, completed: false },
  ]);
  const [weeklyTournament, setWeeklyTournament] = useState({
    title: 'Meme Masters Tournament',
    prize: '$1,000 USDC',
    participants: 1247,
    timeLeft: '3d 12h 45m',
    yourPosition: 47,
  });

  // Enhanced templates with more cultural themes
  const templates: MemeTemplate[] = [
    {
      id: '1',
      name: 'Frog',
      imageUrl: 'https://via.placeholder.com/80x80/4ECDC4/FFFFFF?text=🐸',
      culturalTheme: 'community',
      description: 'Hop to wealth! Community-driven success',
    },
    {
      id: '2',
      name: 'Dog',
      imageUrl: 'https://via.placeholder.com/80x80/FF6B6B/FFFFFF?text=🐕',
      culturalTheme: 'loyalty',
      description: 'Loyal to the community, loyal to the gains',
    },
    {
      id: '3',
      name: 'Hoodie Bear',
      imageUrl: 'https://via.placeholder.com/80x80/FFEAA7/333333?text=🐻',
      culturalTheme: 'resilience',
      description: 'Stay warm, stay strong, stay wealthy',
    },
    {
      id: '4',
      name: 'Lion',
      imageUrl: 'https://via.placeholder.com/80x80/FFD700/333333?text=🦁',
      culturalTheme: 'leadership',
      description: 'Lead the pride to financial freedom',
    },
    {
      id: '5',
      name: 'Phoenix',
      imageUrl: 'https://via.placeholder.com/80x80/FF4500/FFFFFF?text=🔥',
      culturalTheme: 'rebirth',
      description: 'Rise from ashes to financial glory',
    },
  ];

  // Enhanced raids with more data
  const raids: Raid[] = [
    {
      id: '1',
      name: 'Community Frog Raid',
      memeCoin: {
        id: '1',
        name: 'CommunityFrog',
        symbol: 'FROG',
        price: 0.0001,
        change: 12.5,
        holders: 234,
        marketCap: 125000,
        volume24h: 45000,
      },
      targetAmount: 10000,
      currentAmount: 3500,
      participants: 23,
      xpReward: 100,
      timeLeft: '2h 15m',
      isActive: true,
    },
    {
      id: '2',
      name: 'Wealth Dog Pump',
      memeCoin: {
        id: '2',
        name: 'WealthDog',
        symbol: 'DOG',
        price: 0.0002,
        change: 8.3,
        holders: 156,
        marketCap: 89000,
        volume24h: 23000,
      },
      targetAmount: 15000,
      currentAmount: 8900,
      participants: 45,
      xpReward: 150,
      timeLeft: '1h 30m',
      isActive: true,
    },
    {
      id: '3',
      name: 'Lion Pride Rally',
      memeCoin: {
        id: '3',
        name: 'LionPride',
        symbol: 'LION',
        price: 0.0003,
        change: -2.1,
        holders: 89,
        marketCap: 67000,
        volume24h: 12000,
      },
      targetAmount: 20000,
      currentAmount: 12000,
      participants: 67,
      xpReward: 200,
      timeLeft: '45m',
      isActive: true,
    },
  ];

  // DeFi pools for yield farming
  const defiPools: DeFiPool[] = [
    {
      id: '1',
      name: 'ETH/USDC',
      apy: 8.5,
      tvl: 1250000,
      token1: 'ETH',
      token2: 'USDC',
      risk: 'low',
    },
    {
      id: '2',
      name: 'MATIC/USDC',
      apy: 12.3,
      tvl: 890000,
      token1: 'MATIC',
      token2: 'USDC',
      risk: 'medium',
    },
    {
      id: '3',
      name: 'FROG/DOG',
      apy: 25.7,
      tvl: 45000,
      token1: 'FROG',
      token2: 'DOG',
      risk: 'high',
    },
  ];

  // Voice commands mapping
  const voiceCommands = {
    'launch meme': () => launchMeme(),
    'join raid': () => setStep(2),
    'defi yield': () => setStep(3),
    'show templates': () => setStep(1),
    'my xp': () => setShowXPModal(true),
    'streak status': () => setShowStreakModal(true),
    'help': () => setShowVoiceModal(true),
  };

  useEffect(() => {
    // Start pulse animation for voice orb
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    );

    pulse.start();

    return () => {
      pulse.stop();
    };
  }, []);

  const showStreakInfo = () => {
    Alert.alert(
      'Streak Status 🔥',
      `Current Streak: ${currentStreak} days\nNext Reward: ${(currentStreak + 1) * 10} XP\nFreeze Cost: 1 Gem`,
      [{ text: 'Keep Going!', style: 'default' }]
    );
  };

  const showVoiceHelp = () => {
    Alert.alert(
      'Voice Commands 🎤',
      'Available commands:\n• "Launch meme" - Start meme creation\n• "Join raid" - Go to raids\n• "Defi yield" - Go to yield farming\n• "Show templates" - Go to templates\n• "My xp" - Show XP status\n• "Streak status" - Show streak info',
      [{ text: 'Got it!', style: 'default' }]
    );
  };

  const handleVoiceCommand = (command: string) => {
    const normalizedCommand = command.toLowerCase().trim();
    
    for (const [key, action] of Object.entries(voiceCommands)) {
      if (normalizedCommand.includes(key)) {
        action();
        safeSpeak(`Executing ${key} command!`);
        return;
      }
    }
    
    safeSpeak('Command not recognized. Say "help" for available commands.');
  };

  const completeChallenge = (challengeId: number) => {
    setDailyChallenges(prev => 
      prev.map(challenge => 
        challenge.id === challengeId 
          ? { ...challenge, completed: true, progress: challenge.total }
          : challenge
      )
    );
    const reward = dailyChallenges.find(c => c.id === challengeId)?.reward || 0;
    setTotalXP(prev => prev + reward);
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 2000);
    safeSpeak(`Challenge completed! +${reward} XP earned!`);
  };

  const joinTournament = () => {
    setWeeklyTournament(prev => ({
      ...prev,
      participants: prev.participants + 1,
      yourPosition: prev.participants + 1
    }));
    setTotalXP(prev => prev + 50);
    safeSpeak('Joined tournament! +50 XP bonus!');
  };

  const launchMeme = async () => {
    if (!memeName.trim() || !selectedTemplate) {
      Alert.alert('Missing Info', 'Please enter a meme name and select a template!');
      return;
    }

    // Validate required fields
    if (!memeDescription.trim()) {
      Alert.alert('Missing Description', 'Please enter a description for your meme!');
      return;
    }

    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      
      // Real Pump.fun API call simulation
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://192.168.1.236:8000'}/api/pump-fun/launch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: memeName.trim(),
          symbol: memeName.substring(0, 4).toUpperCase(),
          description: memeDescription.trim(),
          template: selectedTemplate.id,
          culturalTheme: selectedTemplate.culturalTheme || 'community',
        }),
      });

      if (response.ok) {
        const result = await response.json();
        safeSpeak(`Launching ${memeName}! Hop to the moon! 🚀`);
        
        setShowConfetti(true);
        
        setTimeout(() => {
          setShowConfetti(false);
          setStep(2);
          setTotalXP(prev => prev + 50);
          setQuestProgress(prev => prev + 1);
          
          Alert.alert(
            'Meme Launched! 🚀',
            `${memeName} has been launched successfully!\nContract: ${result.contractAddress}\nYou earned 50 XP!`,
            [{ text: 'Awesome!', style: 'default' }]
          );
        }, 2000);
      } else {
        // Get detailed error information
        const errorText = await response.text();
        let errorMessage = 'Launch failed';
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        
        throw new Error(errorMessage);
      }
      
    } catch (error) {
      logger.error('MemeQuest Launch Error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      Alert.alert('Launch Failed', `Failed to launch meme: ${errorMessage}`);
    }
  };

  const joinRaid = (raid: Raid) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    Alert.alert(
      'Join Raid? ⚔️',
      `Join ${raid.name} and earn ${raid.xpReward} XP?\n\nTarget: $${raid.targetAmount.toLocaleString()}\nCurrent: $${raid.currentAmount.toLocaleString()}\nTime Left: ${raid.timeLeft}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Join!',
          onPress: () => {
            setTotalXP(prev => prev + raid.xpReward);
            Alert.alert('Raid Joined!', `You joined ${raid.name}! +${raid.xpReward} XP`);
          },
        },
      ]
    );
  };

  const stakeInPool = (pool: DeFiPool) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    Alert.alert(
      'Stake in Pool? 💰',
      `Stake in ${pool.name} pool?\n\nAPY: ${pool.apy}%\nTVL: $${pool.tvl.toLocaleString()}\nRisk: ${pool.risk.toUpperCase()}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stake!',
          onPress: () => {
            setTotalXP(prev => prev + 75);
            Alert.alert('Staked!', `You staked in ${pool.name}! +75 XP`);
          },
        },
      ]
    );
  };

  const renderCreateStep = () => (
    <ScrollView style={styles.createScroll} showsVerticalScrollIndicator={false}>
      <Text style={styles.stepTitle}>Step 1: Craft Your Meme 🎨</Text>
      
      {/* Template Grid */}
      <View style={styles.templateSection}>
        <Text style={styles.sectionTitle}>Choose Your Template</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.templateGrid}>
          {templates.map((template) => (
            <TouchableOpacity
              key={template.id}
              testID={template.name.toLowerCase().includes('frog') ? 'frog-template' : `template-${template.id}`}
              style={[
                styles.templateCard,
                selectedTemplate?.id === template.id && styles.selectedTemplate,
              ]}
              onPress={() => {
                setSelectedTemplate(template);
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                safeSpeak(`Selected ${template.name} template`);
              }}
            >
              <Image source={{ uri: template.imageUrl }} style={styles.templateImage} />
              <Text style={styles.templateLabel}>{template.name}</Text>
              <Text style={styles.templateTheme}>{template.culturalTheme}</Text>
              <Text style={styles.templateDescription}>{template.description}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Input Fields */}
      <View style={styles.inputSection}>
        <Text style={styles.sectionTitle}>Meme Details</Text>
        
        <TextInput
          style={styles.input}
          placeholder="Meme Name (e.g., RichesFrog)"
          value={memeName}
          onChangeText={setMemeName}
          placeholderTextColor="#999"
        />
        
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Description (e.g., Hop to wealth! BIPOC vibes)"
          value={memeDescription}
          onChangeText={setMemeDescription}
          multiline
          numberOfLines={3}
          placeholderTextColor="#999"
        />
      </View>

      {/* Launch Button */}
      <TouchableOpacity testID="animate-button" style={styles.launchButton} onPress={launchMeme}>
        <LinearGradient
          colors={['#4ECDC4', '#44A08D']}
          style={styles.launchGradient}
        >
          <Text style={styles.launchText}>Pump It! 🚀</Text>
        </LinearGradient>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderRaidStep = () => (
    <ScrollView style={styles.raidScroll} showsVerticalScrollIndicator={false}>
      <Text style={styles.stepTitle}>Step 2: Join the Raid! 📈</Text>
      
      {/* Active Raids */}
      <View style={styles.raidsSection}>
        <Text style={styles.sectionTitle}>Active Raids</Text>
        {raids.map((raid) => (
          <View key={raid.id} style={styles.raidCard}>
            <View style={styles.raidHeader}>
              <Text style={styles.raidName}>{raid.name}</Text>
              <View style={styles.raidBadges}>
                <Text style={styles.raidXP}>+{raid.xpReward} XP</Text>
                <Text style={styles.timeLeft}>{raid.timeLeft}</Text>
              </View>
            </View>
            
            <View style={styles.memeInfo}>
              <Text style={styles.memeSymbol}>${raid.memeCoin.symbol}</Text>
              <Text style={styles.memePrice}>${raid.memeCoin.price.toFixed(4)}</Text>
              <Text style={[
                styles.memeChange,
                { color: raid.memeCoin.change >= 0 ? '#4ECDC4' : '#FF6B6B' }
              ]}>
                {raid.memeCoin.change >= 0 ? '+' : ''}{raid.memeCoin.change}%
              </Text>
            </View>
            
            <View style={styles.raidStats}>
              <Text style={styles.statText}>💰 MC: ${raid.memeCoin.marketCap.toLocaleString()}</Text>
              <Text style={styles.statText}>📊 Vol: ${raid.memeCoin.volume24h.toLocaleString()}</Text>
            </View>
            
            <View style={styles.raidProgress}>
              <View style={styles.progressBar}>
                <View style={[
                  styles.progressFill,
                  { width: `${(raid.currentAmount / raid.targetAmount) * 100}%` }
                ]} />
              </View>
              <Text style={styles.progressText}>
                ${raid.currentAmount.toLocaleString()} / ${raid.targetAmount.toLocaleString()}
              </Text>
            </View>
            
            <View style={styles.raidStats}>
              <Text style={styles.statText}>👥 {raid.participants} participants</Text>
              <Text style={styles.statText}>👀 {raid.memeCoin.holders} holders</Text>
            </View>
            
            <TouchableOpacity
              style={styles.joinRaidButton}
              onPress={() => joinRaid(raid)}
            >
              <LinearGradient
                colors={['#FF6B6B', '#FF8E8E']}
                style={styles.joinRaidGradient}
              >
                <Text style={styles.joinRaidText}>Join Raid! ⚔️</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      {/* Social Feed */}
      <View style={styles.socialSection}>
        <Text style={styles.sectionTitle}>Social Feed</Text>
        <SocialFeed />
      </View>
    </ScrollView>
  );

  const renderDeFiStep = () => (
    <ScrollView style={styles.defiScroll} showsVerticalScrollIndicator={false}>
      <Text style={styles.stepTitle}>Step 3: DeFi Yield Farming 💰</Text>
      
      {/* DeFi Pools */}
      <View style={styles.poolsSection}>
        <Text style={styles.sectionTitle}>Available Pools</Text>
        {defiPools.map((pool) => (
          <View key={pool.id} style={styles.poolCard}>
            <View style={styles.poolHeader}>
              <Text style={styles.poolName}>{pool.name}</Text>
              <View style={[
                styles.riskBadge,
                { backgroundColor: pool.risk === 'low' ? '#4ECDC4' : pool.risk === 'medium' ? '#FFEAA7' : '#FF6B6B' }
              ]}>
                <Text style={styles.riskText}>{pool.risk.toUpperCase()}</Text>
              </View>
            </View>
            
            <View style={styles.poolStats}>
              <Text style={styles.apyText}>APY: {pool.apy}%</Text>
              <Text style={styles.tvlText}>TVL: ${pool.tvl.toLocaleString()}</Text>
            </View>
            
            <View style={styles.poolTokens}>
              <Text style={styles.tokenText}>{pool.token1}</Text>
              <Text style={styles.tokenSeparator}>/</Text>
              <Text style={styles.tokenText}>{pool.token2}</Text>
            </View>
            
            <TouchableOpacity
              style={styles.stakeButton}
              onPress={() => stakeInPool(pool)}
            >
              <LinearGradient
                colors={['#4ECDC4', '#44A08D']}
                style={styles.stakeGradient}
              >
                <Text style={styles.stakeText}>Stake & Earn! 💰</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  return (
    <Animated.ScrollView 
      style={styles.container}
      onScroll={Animated.event(
        [{ nativeEvent: { contentOffset: { y: scrollY } } }],
        { useNativeDriver: false }
      )}
      scrollEventThrottle={16}
    >
      {/* Enhanced Header with Tournament Info */}
      <LinearGradient
        colors={['#FF6B6B', '#FFEAA7']}
        style={styles.header}
      >
        <View style={styles.headerTop}>
          <Text style={styles.headerTitle}>🔥 MemeQuest Raid!</Text>
          <TouchableOpacity style={styles.tournamentBadge} onPress={joinTournament}>
            <Text style={styles.tournamentText}>🏆 Tournament</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.headerStats}>
          <TouchableOpacity style={styles.statItem} onPress={() => setShowXPModal(true)}>
            <Text style={styles.statValue}>{totalXP}</Text>
            <Text style={styles.statLabel}>XP</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.statItem} onPress={() => setShowStreakModal(true)}>
            <Text style={styles.statValue}>{currentStreak}</Text>
            <Text style={styles.statLabel}>Streak</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.statItem} onPress={() => setShowXPModal(true)}>
            <Text style={styles.statValue}>#{userRank}</Text>
            <Text style={styles.statLabel}>Rank</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      {/* Enhanced Voice Orb */}
      <Animated.View style={[
        styles.voiceOrb, 
        { 
          transform: [
            { scale: pulseAnim },
            { 
              translateY: scrollY.interpolate({
                inputRange: [0, 1000],
                outputRange: [0, -50],
                extrapolate: 'clamp',
              })
            }
          ] 
        }
      ]}>
        <TouchableOpacity
          testID="voice-launch"
          style={styles.voiceButton}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            setShowVoiceModal(true);
            safeSpeak('Ready to launch? Say your command!');
          }}
        >
          <Text style={styles.voiceIcon}>🎤</Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Step Navigation */}
      <View style={styles.stepNavigation}>
        <TouchableOpacity
          style={[styles.stepButton, step === 1 && styles.activeStep]}
          onPress={() => setStep(1)}
        >
          <Text style={[styles.stepButtonText, step === 1 && styles.activeStepText]}>
            🎨 Create
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.stepButton, step === 2 && styles.activeStep]}
          onPress={() => setStep(2)}
        >
          <Text style={[styles.stepButtonText, step === 2 && styles.activeStepText]}>
            ⚔️ Raid
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.stepButton, step === 3 && styles.activeStep]}
          onPress={() => setStep(3)}
        >
          <Text style={[styles.stepButtonText, step === 3 && styles.activeStepText]}>
            💰 DeFi
          </Text>
        </TouchableOpacity>
      </View>

      {/* Daily Challenges */}
      <View style={styles.challengesSection}>
        <Text style={styles.challengesTitle}>🎯 Daily Challenges</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.challengesScroll}>
          {dailyChallenges.map((challenge) => (
            <TouchableOpacity 
              key={challenge.id} 
              style={[styles.challengeCard, challenge.completed && styles.challengeCompleted]}
              onPress={() => !challenge.completed && completeChallenge(challenge.id)}
            >
              <Text style={styles.challengeTitle}>{challenge.title}</Text>
              <Text style={styles.challengeProgress}>{challenge.progress}/{challenge.total}</Text>
              <Text style={styles.challengeReward}>+{challenge.reward} XP</Text>
              {challenge.completed && <Text style={styles.challengeCheck}>✅</Text>}
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Weekly Tournament */}
      <View style={styles.tournamentSection}>
        <Text style={styles.tournamentTitle}>🏆 {weeklyTournament.title}</Text>
        <View style={styles.tournamentInfo}>
          <Text style={styles.tournamentPrize}>Prize: {weeklyTournament.prize}</Text>
          <Text style={styles.tournamentParticipants}>{weeklyTournament.participants} participants</Text>
          <Text style={styles.tournamentTime}>Time Left: {weeklyTournament.timeLeft}</Text>
          <Text style={styles.tournamentPosition}>Your Position: #{weeklyTournament.yourPosition}</Text>
        </View>
      </View>

      {/* Main Content */}
      {step === 1 && renderCreateStep()}
      {step === 2 && renderRaidStep()}
      {step === 3 && renderDeFiStep()}

      {/* Footer Progress */}
      <View style={styles.footer}>
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${(questProgress / 5) * 100}%` }]} />
          </View>
          <Text style={styles.progressText}>Quest Progress: {questProgress}/5</Text>
        </View>
        
        <TouchableOpacity style={styles.freezeButton}>
          <Text style={styles.freezeText}>Freeze Streak? ❄️ (1 Gem)</Text>
        </TouchableOpacity>
      </View>

      {/* Voice Command Modal */}
      <Modal
        visible={showVoiceModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowVoiceModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Voice Commands 🎤</Text>
            <Text style={styles.modalSubtitle}>Say a command to execute</Text>
            
            <View style={styles.commandList}>
              <Text style={styles.commandItem}>• "Launch meme" - Start meme creation</Text>
              <Text style={styles.commandItem}>• "Join raid" - Go to raids</Text>
              <Text style={styles.commandItem}>• "Defi yield" - Go to yield farming</Text>
              <Text style={styles.commandItem}>• "My xp" - Show XP status</Text>
              <Text style={styles.commandItem}>• "Help" - Show this help</Text>
            </View>
            
            <TouchableOpacity
              style={styles.listenButton}
              onPress={() => {
                setIsListening(!isListening);
                if (!isListening) {
                  safeSpeak('Listening... Say your command');
                } else {
                  safeSpeak('Command received!');
                  handleVoiceCommand('launch meme'); // Simulate command
                  setShowVoiceModal(false);
                }
              }}
            >
              <LinearGradient
                colors={isListening ? ['#FF6B6B', '#FF8E8E'] : ['#4ECDC4', '#44A08D']}
                style={styles.listenGradient}
              >
                <Text style={styles.listenText}>
                  {isListening ? '🎤 Listening...' : '🎤 Start Listening'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setShowVoiceModal(false)}
            >
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Enhanced Leaderboard Modal */}
      <Modal
        visible={showXPModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowXPModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>🏆 Leaderboard</Text>
            <Text style={styles.modalSubtitle}>Top MemeQuest Players</Text>
            <ScrollView style={styles.leaderboardList}>
              {leaderboard.map((player, index) => (
                <View key={player.id} style={[styles.leaderboardItem, index < 3 && styles.topPlayer]}>
                  <Text style={styles.rankNumber}>#{index + 1}</Text>
                  <Text style={styles.playerAvatar}>{player.avatar}</Text>
                  <View style={styles.playerInfo}>
                    <Text style={styles.playerName}>{player.username}</Text>
                    <Text style={styles.playerStats}>{player.xp} XP • {player.streak} day streak</Text>
                  </View>
                  {index < 3 && <Text style={styles.trophy}>🏆</Text>}
                </View>
              ))}
            </ScrollView>
            <TouchableOpacity style={styles.closeButton} onPress={() => setShowXPModal(false)}>
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Confetti */}
      {showConfetti && (
        <ConfettiCannon
          count={150}
          origin={{ x: width / 2, y: 0 }}
          colors={['#FF6B6B', '#4ECDC4', '#FFEAA7']}
        />
      )}
    </Animated.ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF0F5',
  },
  header: {
    padding: 20,
    paddingTop: 50,
    paddingBottom: 25,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    alignItems: 'center',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    width: '100%',
  },
  tournamentBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  tournamentText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  headerStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  streakText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    marginBottom: 4,
  },
  xpText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
  },
  voiceOrb: {
    position: 'absolute',
    top: -10,
    alignSelf: 'center',
    zIndex: 10,
  },
  voiceButton: {
    backgroundColor: '#FF6B6B',
    borderRadius: 30,
    width: 60,
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  voiceIcon: {
    fontSize: 24,
    color: 'white',
  },
  stepNavigation: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    marginBottom: 10,
  },
  stepButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#F0F0F0',
  },
  activeStep: {
    backgroundColor: '#4ECDC4',
  },
  stepButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  activeStepText: {
    color: 'white',
  },
  createScroll: {
    flex: 1,
    padding: 20,
    paddingTop: 15,
  },
  raidScroll: {
    flex: 1,
    padding: 20,
    paddingTop: 15,
  },
  defiScroll: {
    flex: 1,
    padding: 20,
    paddingTop: 15,
  },
  stepTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  templateSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  templateGrid: {
    flexDirection: 'row',
  },
  templateCard: {
    width: 120,
    marginRight: 12,
    alignItems: 'center',
    padding: 12,
    backgroundColor: 'white',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  selectedTemplate: {
    borderWidth: 2,
    borderColor: '#4ECDC4',
  },
  templateImage: {
    width: 60,
    height: 60,
    borderRadius: 30,
    marginBottom: 8,
  },
  templateLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  templateTheme: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginBottom: 4,
  },
  templateDescription: {
    fontSize: 10,
    color: '#999',
    textAlign: 'center',
    lineHeight: 12,
  },
  inputSection: {
    marginBottom: 24,
  },
  input: {
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
    backgroundColor: 'white',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  launchButton: {
    alignItems: 'center',
    marginTop: 20,
  },
  launchGradient: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  launchText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 18,
  },
  raidsSection: {
    marginBottom: 24,
  },
  raidCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  raidHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  raidName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  raidBadges: {
    alignItems: 'flex-end',
  },
  raidXP: {
    fontSize: 14,
    color: '#4ECDC4',
    fontWeight: '600',
  },
  timeLeft: {
    fontSize: 12,
    color: '#FF6B6B',
    fontWeight: '600',
  },
  memeInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  memeSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginRight: 12,
  },
  memePrice: {
    fontSize: 16,
    color: '#666',
    marginRight: 12,
  },
  memeChange: {
    fontSize: 16,
    fontWeight: '600',
  },
  raidProgress: {
    marginBottom: 12,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4ECDC4',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  raidStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  statText: {
    fontSize: 12,
    color: '#666',
  },
  joinRaidButton: {
    alignItems: 'center',
  },
  joinRaidGradient: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
  },
  joinRaidText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  socialSection: {
    marginBottom: 24,
  },
  poolsSection: {
    marginBottom: 24,
  },
  poolCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  poolHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  poolName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  poolStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  apyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4ECDC4',
  },
  tvlText: {
    fontSize: 16,
    color: '#666',
  },
  poolTokens: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  tokenText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  tokenSeparator: {
    fontSize: 14,
    color: '#666',
    marginHorizontal: 8,
  },
  stakeButton: {
    alignItems: 'center',
  },
  stakeGradient: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
  },
  stakeText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  footer: {
    padding: 20,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderColor: '#EEE',
  },
  progressContainer: {
    marginBottom: 12,
  },
  freezeButton: {
    backgroundColor: '#FFF3CD',
    padding: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  freezeText: {
    color: '#856404',
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 24,
    margin: 20,
    maxWidth: width * 0.9,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  commandList: {
    marginBottom: 20,
  },
  commandItem: {
    fontSize: 14,
    color: '#333',
    marginBottom: 8,
    lineHeight: 20,
  },
  listenButton: {
    alignItems: 'center',
    marginBottom: 16,
  },
  listenGradient: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 25,
  },
  listenText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  closeButton: {
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600',
  },
  // Competitive Gaming Styles
  challengesSection: {
    padding: 20,
    paddingTop: 15,
    paddingBottom: 15,
    backgroundColor: '#F8F9FA',
    marginBottom: 10,
  },
  challengesTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  challengesScroll: {
    height: 120,
  },
  challengeCard: {
    width: 140,
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 12,
    marginRight: 10,
    alignItems: 'center',
    elevation: 2,
  },
  challengeCompleted: {
    backgroundColor: '#E8F5E8',
    borderColor: '#4CAF50',
    borderWidth: 2,
  },
  challengeTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 5,
  },
  challengeProgress: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  challengeReward: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  challengeCheck: {
    position: 'absolute',
    top: 5,
    right: 5,
    fontSize: 16,
  },
  tournamentSection: {
    padding: 20,
    paddingTop: 15,
    paddingBottom: 15,
    backgroundColor: '#FFF3E0',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#FFB74D',
    marginBottom: 10,
  },
  tournamentTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  tournamentInfo: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  tournamentPrize: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FF6B6B',
    width: '50%',
  },
  tournamentParticipants: {
    fontSize: 12,
    color: '#666',
    width: '50%',
  },
  tournamentTime: {
    fontSize: 12,
    color: '#666',
    width: '50%',
  },
  tournamentPosition: {
    fontSize: 12,
    color: '#666',
    width: '50%',
  },
  leaderboardList: {
    maxHeight: 300,
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  topPlayer: {
    backgroundColor: '#FFF8E1',
  },
  rankNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    width: 30,
  },
  playerAvatar: {
    fontSize: 24,
    marginHorizontal: 10,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  playerStats: {
    fontSize: 12,
    color: '#666',
  },
  trophy: {
    fontSize: 20,
  },
});

export default MemeQuestScreen;