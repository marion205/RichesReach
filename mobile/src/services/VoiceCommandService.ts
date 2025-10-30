import { Speech } from 'expo-speech';
import * as Haptics from 'expo-haptics';

export interface VoiceCommand {
  id: string;
  type: 'memequest' | 'trading' | 'education' | 'social' | 'defi' | 'general';
  intent: string;
  parameters: Record<string, any>;
  confidence: number;
  context: string;
  response: string;
  action?: () => Promise<void>;
}

export interface VoiceCommandContext {
  userState: {
    isConnected: boolean;
    currentStreak: number;
    totalXP: number;
  };
  portfolio: {
    totalValue: number;
    holdings: Array<{ symbol: string; value: number }>;
  };
  memequest: {
    activeMemes: string[];
    stakedAmount: number;
  };
}

export class VoiceCommandService {
  private context: VoiceCommandContext;
  private commandHistory: VoiceCommand[] = [];

  constructor(initialContext: VoiceCommandContext) {
    this.context = initialContext;
  }

  /**
   * Process voice transcript and return appropriate command
   */
  async processVoiceCommand(transcript: string): Promise<VoiceCommand | null> {
    const normalizedTranscript = transcript.toLowerCase().trim();
    
    // Parse different command types
    const memeQuestCommands = this.parseMemeQuestCommands(normalizedTranscript);
    if (memeQuestCommands) return memeQuestCommands;

    const tradingCommands = this.parseTradingCommands(normalizedTranscript);
    if (tradingCommands) return tradingCommands;

    // Education Commands
    const educationCommands = this.parseEducationCommands(normalizedTranscript);
    if (educationCommands) return educationCommands;

    // Social Commands
    const socialCommands = this.parseSocialCommands(normalizedTranscript);
    if (socialCommands) return socialCommands;

    // DeFi Commands
    const defiCommands = this.parseDeFiCommands(normalizedTranscript);
    if (defiCommands) return defiCommands;

    // General Commands
    const generalCommands = this.parseGeneralCommands(normalizedTranscript);
    if (generalCommands) return generalCommands;

    return null;
  }

  /**
   * Execute a voice command
   */
  async executeCommand(command: VoiceCommand): Promise<void> {
    try {
      // Add to history
      this.commandHistory.push(command);

      // Speak response
      await this.speakResponse(command.response);

      // Execute action
      if (command.action) {
        await command.action();
      }

      // Haptic feedback
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error('Error executing command:', error);
      await this.speakResponse('Sorry, I had trouble executing that command.');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  }

  /**
   * Speak response with voice settings
   */
  private async speakResponse(text: string): Promise<void> {
    try {
      await Speech.speak(text, {
        voice: this.context.userState.isConnected ? 'en-US' : 'en-US',
        rate: 0.9,
        pitch: 1.0,
      });
    } catch (error) {
      console.error('Error speaking response:', error);
    }
  }

  /**
   * Parse MemeQuest-specific commands
   */
  private parseMemeQuestCommands(transcript: string): VoiceCommand | null {
    // Launch meme commands
    if (this.matchesPattern(transcript, ['launch', 'create', 'make', 'start'])) {
      const memeName = this.extractMemeName(transcript);
      const template = this.extractTemplate(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'memequest',
        intent: 'launch_meme',
        parameters: {
          memeName: memeName || 'MyMeme',
          template: template || 'classic',
          description: this.extractDescription(transcript) || 'A new meme!'
        },
        confidence: 0.9,
        context: 'memequest_launch',
        response: `Launching ${memeName || 'MyMeme'} meme! 🚀`,
        action: async () => {
          await this.executeMemeLaunch(memeName || 'MyMeme', template || 'classic');
        }
      };
    }

    // Join raid commands
    if (this.matchesPattern(transcript, ['join', 'raid', 'attack', 'pump'])) {
      const raidId = this.extractRaidId(transcript);
      const amount = this.extractAmount(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'memequest',
        intent: 'join_raid',
        parameters: {
          raidId: raidId || 'current',
          amount: amount || 100
        },
        confidence: 0.8,
        context: 'memequest_raid',
        response: 'Joining the raid! Let\'s pump it up! 💪',
        action: async () => {
          await this.executeRaidJoin(raidId || 'current', amount || 100);
        }
      };
    }

    // Stake for yield commands
    if (this.matchesPattern(transcript, ['stake', 'yield', 'farm', 'earn'])) {
      const memeId = this.extractMemeId(transcript);
      const amount = this.extractAmount(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'memequest',
        intent: 'stake_yield',
        parameters: {
          memeId: memeId || 'current',
          amount: amount || 1000
        },
        confidence: 0.8,
        context: 'memequest_stake',
        response: 'Staking for yield! Let\'s earn those rewards! 🌾',
        action: async () => {
          await this.executeStakeYield(memeId || 'current', amount || 1000);
        }
      };
    }

    return null;
  }

  /**
   * Parse trading commands
   */
  private parseTradingCommands(transcript: string): VoiceCommand | null {
    // Buy commands
    if (this.matchesPattern(transcript, ['buy', 'purchase', 'get'])) {
      const symbol = this.extractSymbol(transcript);
      const amount = this.extractAmount(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'trading',
        intent: 'buy',
        parameters: {
          symbol: symbol || 'BTC',
          amount: amount || 100
        },
        confidence: 0.9,
        context: 'trading_buy',
        response: `Buying ${amount || 100} ${symbol || 'BTC'}! 📈`,
        action: async () => {
          await this.executeBuy(symbol || 'BTC', amount || 100);
        }
      };
    }

    // Sell commands
    if (this.matchesPattern(transcript, ['sell', 'dump', 'liquidate'])) {
      const symbol = this.extractSymbol(transcript);
      const amount = this.extractAmount(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'trading',
        intent: 'sell',
        parameters: {
          symbol: symbol || 'BTC',
          amount: amount || 100
        },
        confidence: 0.9,
        context: 'trading_sell',
        response: `Selling ${amount || 100} ${symbol || 'BTC'}! 📉`,
        action: async () => {
          await this.executeSell(symbol || 'BTC', amount || 100);
        }
      };
    }

    return null;
  }

  /**
   * Parse education commands
   */
  private parseEducationCommands(transcript: string): VoiceCommand | null {
    // Quiz commands
    if (this.matchesPattern(transcript, ['quiz', 'test', 'question', 'challenge'])) {
      const topic = this.extractTopic(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'education',
        intent: 'quiz',
        parameters: {
          topic: topic || 'trading'
        },
        confidence: 0.8,
        context: 'education_quiz',
        response: `Starting ${topic || 'trading'} quiz! Let's test your knowledge! 🧠`,
        action: async () => {
          await this.executeQuiz(topic || 'trading');
        }
      };
    }

    // Learn commands
    if (this.matchesPattern(transcript, ['learn', 'teach', 'explain', 'show'])) {
      const topic = this.extractTopic(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'education',
        intent: 'learn',
        parameters: {
          topic: topic || 'trading'
        },
        confidence: 0.8,
        context: 'education_learn',
        response: `Teaching you about ${topic || 'trading'}! 📚`,
        action: async () => {
          await this.executeLearn(topic || 'trading');
        }
      };
    }

    return null;
  }

  /**
   * Parse social commands
   */
  private parseSocialCommands(transcript: string): VoiceCommand | null {
    // Post commands
    if (this.matchesPattern(transcript, ['post', 'share', 'upload', 'publish'])) {
      const content = this.extractContent(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'social',
        intent: 'create_post',
        parameters: {
          content: content || 'Check this out!'
        },
        confidence: 0.8,
        context: 'social_post',
        response: `Creating post: ${content || 'Check this out!'} 📱`,
        action: async () => {
          await this.executeCreatePost(content || 'Check this out!');
        }
      };
    }

    return null;
  }

  /**
   * Parse DeFi commands
   */
  private parseDeFiCommands(transcript: string): VoiceCommand | null {
    // Yield farming commands
    if (this.matchesPattern(transcript, ['yield', 'farm', 'liquidity', 'provide'])) {
      const protocol = this.extractProtocol(transcript);
      const amount = this.extractAmount(transcript);
      
      return {
        id: this.generateCommandId(),
        type: 'defi',
        intent: 'yield_farm',
        parameters: {
          protocol: protocol || 'Uniswap',
          amount: amount || 1000
        },
        confidence: 0.8,
        context: 'defi_yield',
        response: `Starting yield farming on ${protocol || 'Uniswap'} with ${amount || 1000}! 🌾`,
        action: async () => {
          await this.executeYieldFarm(protocol || 'Uniswap', amount || 1000);
        }
      };
    }

    return null;
  }

  /**
   * Parse general commands
   */
  private parseGeneralCommands(transcript: string): VoiceCommand | null {
    // Help commands
    if (this.matchesPattern(transcript, ['help', 'what can you do', 'commands'])) {
      return {
        id: this.generateCommandId(),
        type: 'general',
        intent: 'help',
        parameters: {},
        confidence: 0.9,
        context: 'general_help',
        response: 'I can help you with memes, trading, learning, and DeFi! Try saying "launch a meme" or "buy Bitcoin"',
        action: async () => {
          await this.executeShowHelp();
        }
      };
    }

    // Status commands
    if (this.matchesPattern(transcript, ['status', 'how am i doing', 'progress'])) {
      return {
        id: this.generateCommandId(),
        type: 'general',
        intent: 'status',
        parameters: {},
        confidence: 0.9,
        context: 'general_status',
        response: `You're doing great! Streak: ${this.context.userState.currentStreak} days, XP: ${this.context.userState.totalXP}`,
        action: async () => {
          await this.executeShowStatus();
        }
      };
    }

    return null;
  }

  // Helper methods for extracting parameters
  private matchesPattern(text: string, patterns: string[]): boolean {
    return patterns.some(pattern => text.includes(pattern));
  }

  private extractMemeName(text: string): string | null {
    // Simple extraction - look for words after "launch" or "create"
    const match = text.match(/(?:launch|create|make|start)\s+(\w+)/);
    return match ? match[1] : null;
  }

  private extractTemplate(text: string): string | null {
    const templates = ['classic', 'modern', 'vintage', 'minimal'];
    return templates.find(template => text.includes(template)) || null;
  }

  private extractDescription(text: string): string | null {
    // Extract text in quotes or after "about"
    const quoteMatch = text.match(/"([^"]+)"/);
    if (quoteMatch) return quoteMatch[1];
    
    const aboutMatch = text.match(/about\s+(.+)/);
    return aboutMatch ? aboutMatch[1] : null;
  }

  private extractRaidId(text: string): string | null {
    // Look for raid ID patterns
    const match = text.match(/raid\s+(\w+)/);
    return match ? match[1] : null;
  }

  private extractAmount(text: string): number | null {
    // Extract numbers from text
    const match = text.match(/(\d+)/);
    return match ? parseInt(match[1]) : null;
  }

  private extractMemeId(text: string): string | null {
    // Look for meme ID patterns
    const match = text.match(/meme\s+(\w+)/);
    return match ? match[1] : null;
  }

  private extractSymbol(text: string): string | null {
    // Common crypto symbols
    const symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOGE', 'SHIB'];
    return symbols.find(symbol => text.includes(symbol.toLowerCase())) || null;
  }

  private extractTopic(text: string): string | null {
    const topics = ['trading', 'crypto', 'defi', 'stocks', 'options'];
    return topics.find(topic => text.includes(topic)) || null;
  }

  private extractContent(text: string): string | null {
    // Extract text after "post" or "share"
    const match = text.match(/(?:post|share|upload|publish)\s+(.+)/);
    return match ? match[1] : null;
  }

  private extractProtocol(text: string): string | null {
    const protocols = ['Uniswap', 'SushiSwap', 'PancakeSwap', 'Compound', 'Aave'];
    return protocols.find(protocol => text.includes(protocol.toLowerCase())) || null;
  }

  private generateCommandId(): string {
    return `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Action execution methods
  private async executeMemeLaunch(memeName: string, template: string): Promise<void> {
    try {
      const response = await fetch('/api/pump-fun/launch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: memeName,
          template: template,
          description: `Voice-launched meme: ${memeName}`,
        }),
      });

      const result = await response.json();

      if (result.success) {
        await this.speakResponse(`Meme ${memeName} launched successfully!`);
      } else {
        await this.speakResponse(`Failed to launch meme: ${result.error}`);
      }
    } catch (error) {
      console.error('Error launching meme:', error);
      await this.speakResponse('Sorry, I had trouble launching the meme.');
    }
  }

  private async executeRaidJoin(raidId: string, amount: number): Promise<void> {
    try {
      const response = await fetch('/api/social/join-raid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          raidId: raidId,
          amount: amount,
        }),
      });

      const result = await response.json();

      if (result.success) {
        await this.speakResponse(`Joined raid ${raidId} with ${amount}!`);
      } else {
        await this.speakResponse(`Failed to join raid: ${result.error}`);
      }
    } catch (error) {
      console.error('Error joining raid:', error);
      await this.speakResponse('Sorry, I had trouble joining the raid.');
    }
  }

  private async executeStakeYield(memeId: string, amount: number): Promise<void> {
    try {
      const response = await fetch('/api/pump-fun/stake-yield', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          memeId: memeId,
          amount: amount,
        }),
      });

      const result = await response.json();

      if (result.success) {
        await this.speakResponse(`Staked ${amount} for yield on ${memeId}!`);
      } else {
        await this.speakResponse(`Failed to stake: ${result.error}`);
      }
    } catch (error) {
      console.error('Error staking:', error);
      await this.speakResponse('Sorry, I had trouble staking.');
    }
  }

  private async executeBuy(symbol: string, amount: number): Promise<void> {
    await this.speakResponse(`Buying ${amount} ${symbol}...`);
    // Implement actual buy logic here
  }

  private async executeSell(symbol: string, amount: number): Promise<void> {
    await this.speakResponse(`Selling ${amount} ${symbol}...`);
    // Implement actual sell logic here
  }

  private async executeQuiz(topic: string): Promise<void> {
    await this.speakResponse(`Starting ${topic} quiz...`);
    // Implement quiz logic here
  }

  private async executeLearn(topic: string): Promise<void> {
    await this.speakResponse(`Teaching you about ${topic}...`);
    // Implement learning logic here
  }

  private async executeCreatePost(content: string): Promise<void> {
    await this.speakResponse(`Creating post: ${content}...`);
    // Implement post creation logic here
  }

  private async executeYieldFarm(protocol: string, amount: number): Promise<void> {
    await this.speakResponse(`Starting yield farming on ${protocol} with ${amount}...`);
    // Implement yield farming logic here
  }

  private async executeShowHelp(): Promise<void> {
    await this.speakResponse('I can help you with memes, trading, learning, and DeFi! Try saying "launch a meme" or "buy Bitcoin"');
  }

  private async executeShowStatus(): Promise<void> {
    await this.speakResponse(`You're doing great! Streak: ${this.context.userState.currentStreak} days, XP: ${this.context.userState.totalXP}`);
  }

  // Context management
  public updateContext(newContext: Partial<VoiceCommandContext>): void {
    this.context = { ...this.context, ...newContext };
  }

  public getCommandHistory(): VoiceCommand[] {
    return [...this.commandHistory];
  }

  public clearCommandHistory(): void {
    this.commandHistory = [];
  }

  public getLastCommand(): VoiceCommand | null {
    return this.commandHistory.length > 0 ? this.commandHistory[this.commandHistory.length - 1] : null;
  }
}

export default VoiceCommandService;