/**
 * Licensing Disclosure Screen
 * Displays regulatory, licensing, terms, privacy, cybersecurity, and pricing information
 * Critical for Apple App Store approval (Guideline 3.1.5(viii))
 * 
 * Includes:
 * - Regulatory & Licensing Info (Stock Trading, Crypto, Risk Disclosures)
 * - Terms & Conditions
 * - Privacy Policy
 * - Cybersecurity Policy
 * - Pricing and Fee Agreement
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Linking,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import logger from '../utils/logger';

// ─── Types ───────────────────────────────────────────────────────────────────

interface LicensingDisclosureScreenProps {
  onClose?: () => void;
  /** Which tab to show initially */
  initialTab?: TabKey;
}

type TabKey = 'regulatory' | 'terms' | 'privacy' | 'cybersecurity' | 'pricing';

interface TabConfig {
  key: TabKey;
  label: string;
  icon: string;
  color: string;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const TABS: TabConfig[] = [
  { key: 'regulatory', label: 'Regulatory', icon: 'shield-checkmark', color: '#22C55E' },
  { key: 'terms', label: 'Terms', icon: 'document-text', color: '#007AFF' },
  { key: 'privacy', label: 'Privacy', icon: 'lock-closed', color: '#8B5CF6' },
  { key: 'cybersecurity', label: 'Security', icon: 'key', color: '#EF4444' },
  { key: 'pricing', label: 'Pricing', icon: 'pricetag', color: '#F59E0B' },
];

// ─── Main Component ──────────────────────────────────────────────────────────

const LicensingDisclosureScreen: React.FC<LicensingDisclosureScreenProps> = ({
  onClose,
  initialTab = 'regulatory',
}) => {
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);

  const openLink = (url: string) => {
    Linking.openURL(url).catch((err) => logger.error('Failed to open URL:', err));
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'regulatory':
        return <RegulatoryTab openLink={openLink} />;
      case 'terms':
        return <TermsTab openLink={openLink} />;
      case 'privacy':
        return <PrivacyTab openLink={openLink} />;
      case 'cybersecurity':
        return <CybersecurityTab openLink={openLink} />;
      case 'pricing':
        return <PricingTab openLink={openLink} />;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Policies & Agreements</Text>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#333" />
          </TouchableOpacity>
        )}
      </View>

      {/* Tab Bar */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabBar}
        contentContainerStyle={styles.tabBarContent}
      >
        {TABS.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Ionicons
              name={tab.icon as any}
              size={18}
              color={activeTab === tab.key ? tab.color : '#9CA3AF'}
            />
            <Text
              style={[
                styles.tabLabel,
                activeTab === tab.key && { color: tab.color, fontWeight: '700' },
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {renderContent()}

        {/* Universal Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>Effective Date: February 5, 2026</Text>
          <Text style={styles.footerText}>
            Last Updated:{' '}
            {new Date().toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ─── Shared Sub-Components ───────────────────────────────────────────────────

const Section: React.FC<{
  icon: string;
  iconColor: string;
  title: string;
  children: React.ReactNode;
}> = ({ icon, iconColor, title, children }) => (
  <View style={styles.section}>
    <View style={styles.sectionHeader}>
      <Ionicons name={icon as any} size={24} color={iconColor} />
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
    {children}
  </View>
);

const DisclosureBox: React.FC<{
  title: string;
  body: string;
  borderColor?: string;
}> = ({ title, body, borderColor = '#007AFF' }) => (
  <View style={[styles.disclosureBox, { borderLeftColor: borderColor }]}>
    <Text style={styles.disclosureTextBold}>{title}</Text>
    <Text style={styles.disclosureText}>{body}</Text>
  </View>
);

const InfoRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={styles.infoValue}>{value}</Text>
  </View>
);

const Bullet: React.FC<{ text: string }> = ({ text }) => (
  <View style={styles.bulletPoint}>
    <Text style={styles.bullet}>•</Text>
    <Text style={styles.bulletText}>{text}</Text>
  </View>
);

const WarningBox: React.FC<{ text: string; color?: string; bgColor?: string }> = ({
  text,
  color = '#92400E',
  bgColor = '#FEF3C7',
}) => (
  <View style={[styles.warningBox, { backgroundColor: bgColor }]}>
    <Ionicons name="information-circle" size={20} color={color} />
    <Text style={[styles.warningText, { color }]}>{text}</Text>
  </View>
);

const LinkButton: React.FC<{ text: string; onPress: () => void }> = ({ text, onPress }) => (
  <TouchableOpacity style={styles.linkButton} onPress={onPress}>
    <Text style={styles.linkText}>{text}</Text>
    <Ionicons name="open-outline" size={16} color="#007AFF" />
  </TouchableOpacity>
);

const SubHeading: React.FC<{ text: string }> = ({ text }) => (
  <Text style={styles.subHeading}>{text}</Text>
);

const Paragraph: React.FC<{ text: string }> = ({ text }) => (
  <Text style={styles.paragraph}>{text}</Text>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 1: REGULATORY & LICENSING
// ═══════════════════════════════════════════════════════════════════════════════

const RegulatoryTab: React.FC<{ openLink: (url: string) => void }> = ({ openLink }) => (
  <View>
    {/* Stock Trading */}
    <Section icon="checkmark-circle" iconColor="#22C55E" title="Stock Trading Services">
      <DisclosureBox
        title="Securities trading is provided through Alpaca Securities LLC, a registered broker-dealer."
        body="Alpaca Securities LLC is a member of the Financial Industry Regulatory Authority (FINRA) and the Securities Investor Protection Corporation (SIPC)."
      />
      <InfoRow label="Broker-Dealer:" value="Alpaca Securities LLC" />
      <InfoRow label="FINRA Member:" value="Yes (Member #289946)" />
      <InfoRow label="SIPC Protection:" value="Yes (Up to $500,000)" />
      <LinkButton
        text="View Alpaca's FINRA BrokerCheck"
        onPress={() => openLink('https://brokercheck.finra.org/firm/summary/289946')}
      />
      <LinkButton
        text="Learn About SIPC Protection"
        onPress={() => openLink('https://www.sipc.org/for-investors/what-sipc-protects')}
      />
      <WarningBox text="RichesReach is not affiliated with Alpaca Securities LLC. Alpaca does not endorse or recommend any particular investment strategy." />
    </Section>

    {/* Crypto */}
    <Section icon="alert-circle" iconColor="#F59E0B" title="Cryptocurrency Trading">
      <DisclosureBox
        title="Cryptocurrency trading is currently not available."
        body="We are working to obtain the necessary regulatory licenses to offer cryptocurrency trading services. This feature will be available in the future once all regulatory requirements are met."
        borderColor="#F59E0B"
      />
      <InfoRow label="Status:" value="Not Available" />
      <InfoRow label="Reason:" value="Regulatory Compliance" />
    </Section>

    {/* Investment Info */}
    <Section icon="school" iconColor="#007AFF" title="Investment Information">
      <DisclosureBox
        title="Not Investment Advice"
        body="All investment information, analysis, recommendations, and educational content provided by RichesReach are for educational and informational purposes only. This is not investment advice, financial planning advice, or a recommendation to buy or sell securities."
      />
      <Bullet text="AI recommendations are based on algorithms and market data, not individual circumstances" />
      <Bullet text="You should consult with a qualified financial advisor before making investment decisions" />
      <Bullet text="Past performance does not guarantee future results" />
      <Bullet text="All investments carry risk of loss" />
    </Section>

    {/* Risk Disclosure */}
    <Section icon="warning" iconColor="#EF4444" title="Risk Disclosure">
      <DisclosureBox
        title="Trading involves substantial risk of loss."
        body="You may lose more than your initial investment. Market conditions can change rapidly and unpredictably. Only invest money you can afford to lose."
        borderColor="#EF4444"
      />
      <Bullet text="All investments carry risk of loss" />
      <Bullet text="Past performance does not guarantee future results" />
      <Bullet text="Market volatility can result in significant losses" />
      <Bullet text="Diversification does not guarantee profit or protect against loss" />
    </Section>

    {/* Contact */}
    <Section icon="mail" iconColor="#007AFF" title="Contact & Support">
      <InfoRow label="Support Email:" value="support@richesreach.com" />
      <InfoRow label="Legal Email:" value="legal@richesreach.com" />
    </Section>
  </View>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 2: TERMS & CONDITIONS
// ═══════════════════════════════════════════════════════════════════════════════

const TermsTab: React.FC<{ openLink: (url: string) => void }> = ({ openLink }) => (
  <View>
    {/* 1. Agreement to Terms */}
    <Section icon="document-text" iconColor="#007AFF" title="1. Agreement to Terms">
      <Paragraph text='By accessing and using the RichesReach mobile application, website, and services ("Platform"), you agree to be bound by these Terms & Conditions ("Terms"). If you do not agree to abide by the above, please do not use this service.' />
    </Section>

    {/* 2. Use License */}
    <Section icon="key" iconColor="#007AFF" title="2. Use License">
      <Paragraph text="Permission is granted to temporarily download one copy of the materials (information or software) on RichesReach's Platform for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:" />
      <Bullet text="Modify or copy the materials" />
      <Bullet text="Use the materials for any commercial purpose or for any public display" />
      <Bullet text="Attempt to decompile or reverse engineer any software contained on RichesReach's Platform" />
      <Bullet text="Remove any copyright or other proprietary notations from the materials" />
      <Bullet text='Transfer the materials to another person or "mirror" the materials on any other server' />
      <Bullet text="Violate any laws or regulations" />
    </Section>

    {/* 3. Investment and Trading Disclaimers */}
    <Section icon="trending-up" iconColor="#007AFF" title="3. Investment & Trading Disclaimers">
      <SubHeading text="3.1 Not Investment Advice" />
      <Paragraph text="RichesReach does not provide personalized investment advice. Information provided on the Platform is for educational purposes only and should not be construed as investment recommendations or advice. Past performance is not indicative of future results." />

      <SubHeading text="3.2 Risk Acknowledgment" />
      <Paragraph text="Trading stocks, options, cryptocurrencies, and other financial instruments involves substantial risk of loss. You acknowledge that:" />
      <Bullet text="You understand the risks associated with trading" />
      <Bullet text="You have sufficient knowledge and experience to make trading decisions" />
      <Bullet text="You are financially able to bear the loss of your investment" />
      <Bullet text="You have read and understand all risk disclosures" />

      <SubHeading text="3.3 No Guaranteed Returns" />
      <Paragraph text="RichesReach's AI recommendations, repair systems, and predictive models are provided 'as-is' without warranty of accuracy or profitability. No algorithm guarantees trading success." />

      <SubHeading text="3.4 Market Volatility" />
      <Paragraph text="Market conditions can change rapidly. All trades are executed at your sole risk and discretion." />
    </Section>

    {/* 4. Brokerage Services */}
    <Section icon="business" iconColor="#007AFF" title="4. Brokerage Services">
      <SubHeading text="4.1 Third-Party Broker Integration" />
      <Paragraph text="RichesReach facilitates trading through partner brokers including but not limited to Alpaca Securities LLC. You are responsible for:" />
      <Bullet text="Maintaining an active account with our partner broker(s)" />
      <Bullet text="Funding your account appropriately" />
      <Bullet text="Understanding broker-specific fees and requirements" />
      <Bullet text="Complying with all broker terms and conditions" />

      <SubHeading text="4.2 Execution Risk" />
      <Paragraph text="RichesReach does not guarantee order execution price, timing, or fill rates. All orders are subject to broker policies and market conditions." />

      <SubHeading text="4.3 Account Security" />
      <Paragraph text="You are solely responsible for maintaining the confidentiality of your login credentials and account information. RichesReach is not liable for unauthorized access resulting from your negligence." />
    </Section>

    {/* 5. Cryptocurrency and DeFi */}
    <Section icon="logo-bitcoin" iconColor="#F59E0B" title="5. Cryptocurrency & DeFi Disclaimer">
      <SubHeading text="5.1 Volatile Assets" />
      <Paragraph text="Cryptocurrency and DeFi assets are highly volatile and speculative. RichesReach's features for crypto/DeFi (vaults, staking, swaps) carry substantial additional risk:" />
      <Bullet text="Smart contract risks" />
      <Bullet text="Impermanent loss (for liquidity pools)" />
      <Bullet text="Smart contract hacks and exploits" />
      <Bullet text="Regulatory uncertainty" />
      <Bullet text="Total loss of capital is possible" />

      <SubHeading text="5.2 Not Regulated Like Traditional Securities" />
      <Paragraph text="Cryptocurrency trading is largely unregulated in the United States and many jurisdictions. Users trade at their own risk." />

      <SubHeading text="5.3 Tax Reporting" />
      <Paragraph text="Users are responsible for calculating and reporting all cryptocurrency transactions for tax purposes. RichesReach does not provide tax advice." />
    </Section>

    {/* 6. AI Coach */}
    <Section icon="chatbubbles" iconColor="#007AFF" title="6. AI Coach & Educational Content">
      <SubHeading text="6.1 Educational Purpose Only" />
      <Paragraph text="All AI-generated recommendations, coaching suggestions, and educational content are provided for learning purposes only. They do not constitute investment advice." />

      <SubHeading text="6.2 Voice Assistant" />
      <Paragraph text="The AI voice assistant is an automated system and should not be relied upon for complex financial decisions. Always conduct your own due diligence." />

      <SubHeading text="6.3 Accuracy" />
      <Paragraph text="While we strive for accuracy, RichesReach makes no guarantee that all educational content or AI recommendations are error-free or current." />
    </Section>

    {/* 7. Option Repair System */}
    <Section icon="construct" iconColor="#007AFF" title='7. Option Repair System ("Active Repairs")'>
      <SubHeading text="7.1 Repair Suggestions" />
      <Paragraph text="RichesReach's 'Active Repairs' system analyzes your options positions and suggests defensive adjustments (repair plans). These suggestions are:" />
      <Bullet text="Generated by algorithms, not financial advisors" />
      <Bullet text="Not guaranteed to improve your position" />
      <Bullet text="Subject to market conditions and execution risk" />
      <Bullet text="Presented for educational understanding only" />

      <SubHeading text="7.2 User Responsibility" />
      <Paragraph text="You alone are responsible for deciding whether to execute a repair plan. RichesReach does not manage your account or execute trades without your explicit authorization." />

      <SubHeading text="7.3 Greeks Calculations" />
      <Paragraph text="Greeks (Delta, Gamma, Theta, Vega, Rho) are calculated using Black-Scholes and other models. Actual Greeks may vary from calculated values." />
    </Section>

    {/* 8. Fees and Pricing */}
    <Section icon="pricetag" iconColor="#007AFF" title="8. Fees and Pricing">
      <SubHeading text="8.1 Subscription Fees" />
      <Bullet text="Free Tier: $0/month (limited features)" />
      <Bullet text="Premium: $19.99/month (advanced analytics + AI features)" />
      <Bullet text="Pro: $49.99/month (HFT system + priority execution)" />
      <Paragraph text="Fees are billed monthly. Cancellation can be done anytime through settings." />

      <SubHeading text="8.2 Trading Fees" />
      <Paragraph text="RichesReach may receive Payment for Order Flow (PFOF) from broker partners. This does not increase your trading costs but may influence order routing." />

      <SubHeading text="8.3 Cryptocurrency Spreads" />
      <Paragraph text="Crypto trades include 1-2% spread on buy/sell prices." />

      <SubHeading text="8.4 DeFi Performance Fees" />
      <Paragraph text="Vault yields include a 0.5% annual performance fee deducted from returns." />
    </Section>

    {/* 9. Limitation of Liability */}
    <Section icon="shield" iconColor="#EF4444" title="9. Limitation of Liability">
      <SubHeading text="9.1 Disclaimer" />
      <Paragraph text="RichesReach and its officers, directors, employees, and agents shall not be liable for:" />
      <Bullet text="Trading losses or unrealized losses" />
      <Bullet text="Data loss or corruption" />
      <Bullet text="Service interruptions" />
      <Bullet text="Third-party broker errors or failures" />
      <Bullet text="Market crashes or extreme volatility" />
      <Bullet text="AI model inaccuracies or failures" />
      <Bullet text="Smart contract exploits or hacks" />

      <SubHeading text="9.2 Maximum Liability" />
      <Paragraph text="To the fullest extent permitted by law, RichesReach's total liability shall not exceed the amount paid by you to RichesReach in the 12 months preceding the claim." />

      <SubHeading text="9.3 Force Majeure" />
      <Paragraph text="RichesReach is not liable for interruptions caused by acts of God, war, terrorism, pandemic, or other events beyond reasonable control." />
    </Section>

    {/* 10. Indemnification */}
    <Section icon="hand-left" iconColor="#007AFF" title="10. Indemnification">
      <Paragraph text="You agree to indemnify and hold harmless RichesReach, its officers, directors, employees, and agents from any claims, damages, losses, or liabilities arising from:" />
      <Bullet text="Your use of the Platform" />
      <Bullet text="Your trading decisions" />
      <Bullet text="Your violation of these Terms" />
      <Bullet text="Your violation of applicable laws" />
    </Section>

    {/* 11. Termination */}
    <Section icon="close-circle" iconColor="#EF4444" title="11. Termination">
      <Paragraph text="RichesReach reserves the right to suspend or terminate your account immediately if you:" />
      <Bullet text="Violate these Terms" />
      <Bullet text="Engage in fraud or market manipulation" />
      <Bullet text="Use the Platform for illegal purposes" />
      <Bullet text="Violate applicable securities or cryptocurrency laws" />
    </Section>

    {/* 12. Modifications */}
    <Section icon="create" iconColor="#007AFF" title="12. Modifications to Terms">
      <Paragraph text="RichesReach may modify these Terms at any time. Your continued use of the Platform constitutes acceptance of modified Terms. We will notify you of material changes via email or in-app notification." />
    </Section>

    {/* 13. Governing Law */}
    <Section icon="globe" iconColor="#007AFF" title="13. Governing Law">
      <Paragraph text="These Terms are governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of law principles." />
    </Section>

    {/* 14. Dispute Resolution */}
    <Section icon="git-compare" iconColor="#007AFF" title="14. Dispute Resolution">
      <SubHeading text="14.1 Arbitration Agreement" />
      <Paragraph text="You agree that any dispute arising out of or relating to the Platform shall be resolved by binding arbitration administered by JAMS, except for claims that cannot be arbitrated under applicable law." />

      <SubHeading text="14.2 Class Action Waiver" />
      <Paragraph text="You waive the right to participate in class actions or class arbitration against RichesReach." />
    </Section>

    {/* 15. Contact */}
    <Section icon="mail" iconColor="#007AFF" title="15. Contact Us">
      <InfoRow label="Email:" value="legal@richesreach.com" />
      <WarningBox text="ACKNOWLEDGMENT: By using RichesReach, you acknowledge that you have read, understood, and agree to be bound by these Terms & Conditions." />
    </Section>
  </View>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 3: PRIVACY POLICY
// ═══════════════════════════════════════════════════════════════════════════════

const PrivacyTab: React.FC<{ openLink: (url: string) => void }> = ({ openLink }) => (
  <View>
    {/* 1. Introduction */}
    <Section icon="information-circle" iconColor="#8B5CF6" title="1. Introduction">
      <Paragraph text='RichesReach ("we," "us," "our," or "Company") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application, website, and services ("Platform").' />
      <Paragraph text="Please read this Privacy Policy carefully. If you do not agree with our policies and practices, please do not use our Platform." />
    </Section>

    {/* 2. Information We Collect */}
    <Section icon="clipboard" iconColor="#8B5CF6" title="2. Information We Collect">
      <SubHeading text="2.1 Information You Provide Directly" />

      <Text style={styles.miniHeading}>Account Registration:</Text>
      <Bullet text="Full name" />
      <Bullet text="Email address" />
      <Bullet text="Phone number" />
      <Bullet text="Date of birth" />
      <Bullet text="Social Security Number (for KYC/AML verification)" />
      <Bullet text="Address and residential information" />
      <Bullet text="Employment information" />

      <Text style={styles.miniHeading}>Financial Information:</Text>
      <Bullet text="Bank account details (for deposits/withdrawals)" />
      <Bullet text="Broker account credentials (via secure OAuth integration)" />
      <Bullet text="Trading history and positions" />
      <Bullet text="Portfolio holdings and valuations" />
      <Bullet text="Account balances and transaction history" />

      <Text style={styles.miniHeading}>Communication:</Text>
      <Bullet text="Messages you send to our support team" />
      <Bullet text="Feedback and survey responses" />
      <Bullet text="Voice commands and audio input (for voice assistant)" />

      <SubHeading text="2.2 Information Collected Automatically" />

      <Text style={styles.miniHeading}>Device Information:</Text>
      <Bullet text="Device type, model, and OS" />
      <Bullet text="IP address" />
      <Bullet text="Device identifiers (IDFA, AAID)" />
      <Bullet text="Browser type and language" />

      <Text style={styles.miniHeading}>Usage Information:</Text>
      <Bullet text="Pages/screens accessed" />
      <Bullet text="Features used" />
      <Bullet text="Time and duration of activities" />
      <Bullet text="Search queries" />
      <Bullet text="Clicks and interactions" />

      <Text style={styles.miniHeading}>Location Information:</Text>
      <Bullet text="Approximate location (based on IP address)" />
      <Bullet text="Precise location (only if you grant permission)" />

      <Text style={styles.miniHeading}>Trading Activity:</Text>
      <Bullet text="Order placement and execution" />
      <Bullet text="Search history within the app" />
      <Bullet text="Price alerts and watchlists" />
      <Bullet text="Preferences and settings" />

      <Text style={styles.miniHeading}>Cookies and Similar Technologies:</Text>
      <Bullet text="Session cookies" />
      <Bullet text="Persistent cookies" />
      <Bullet text="Web beacons and pixels" />
      <Bullet text="Local storage data" />

      <SubHeading text="2.3 Third-Party Information" />
      <Bullet text="Data from broker partners (Alpaca, etc.)" />
      <Bullet text="Market data from financial data providers" />
      <Bullet text="Credit bureau information (for KYC)" />
      <Bullet text="Social media data (if you link accounts)" />
    </Section>

    {/* 3. How We Use Your Information */}
    <Section icon="cog" iconColor="#8B5CF6" title="3. How We Use Your Information">
      <SubHeading text="3.1 Service Provision" />
      <Bullet text="Create and maintain your account" />
      <Bullet text="Execute trades and process transactions" />
      <Bullet text="Provide customer support" />
      <Bullet text="Send transactional emails and notifications" />
      <Bullet text="Verify your identity (KYC/AML compliance)" />
      <Bullet text="Comply with regulatory requirements" />

      <SubHeading text="3.2 Personalization" />
      <Bullet text="Customize your experience" />
      <Bullet text="Provide AI-powered recommendations" />
      <Bullet text="Personalize educational content (IRT-based learning)" />
      <Bullet text="Tailor marketing messages" />

      <SubHeading text="3.3 Analytics and Improvement" />
      <Bullet text="Analyze usage patterns" />
      <Bullet text="Improve Platform features and performance" />
      <Bullet text="Conduct A/B testing" />
      <Bullet text="Understand user demographics" />

      <SubHeading text="3.4 Marketing and Communications" />
      <Bullet text="Send promotional emails (with opt-out option)" />
      <Bullet text="Notify you about new features" />
      <Bullet text="Invite you to events or webinars" />
      <Bullet text="Conduct surveys and gather feedback" />

      <SubHeading text="3.5 Security and Fraud Prevention" />
      <Bullet text="Monitor for fraudulent activity" />
      <Bullet text="Prevent unauthorized access" />
      <Bullet text="Protect against hacking attempts" />
      <Bullet text="Audit and secure systems" />

      <SubHeading text="3.6 Legal Compliance" />
      <Bullet text="Comply with SEC, FINRA, and FinCEN regulations" />
      <Bullet text="Respond to legal requests from law enforcement" />
      <Bullet text="Maintain records required by financial regulations" />
      <Bullet text="Report suspicious activity (SAR filing)" />
    </Section>

    {/* 4. How We Share Your Information */}
    <Section icon="share-social" iconColor="#8B5CF6" title="4. How We Share Your Information">
      <SubHeading text="4.1 Service Providers" />
      <Bullet text="Broker partners (Alpaca, etc.) – for trade execution" />
      <Bullet text="Payment processors – for deposits/withdrawals" />
      <Bullet text="Cloud providers (AWS) – for data storage" />
      <Bullet text="Analytics providers – for usage analysis" />
      <Bullet text="Customer support platforms – for assistance" />

      <SubHeading text="4.2 Legal Requirements" />
      <Bullet text="Court orders or subpoenas" />
      <Bullet text="Government agencies (SEC, IRS, FinCEN)" />
      <Bullet text="Law enforcement investigations" />
      <Bullet text="To protect legal rights" />

      <SubHeading text="4.3 Business Transfers" />
      <Paragraph text="If RichesReach is acquired or merges, your information may be transferred as part of that transaction. You will be notified of any change in ownership or use of personal information." />

      <SubHeading text="4.4 With Your Consent" />
      <Paragraph text="We may share information with third parties if you explicitly consent." />

      <SubHeading text="4.5 Aggregate and Anonymized Data" />
      <Paragraph text="We may share de-identified, aggregate data about user behavior with marketing partners and researchers." />
    </Section>

    {/* 5. Data Security */}
    <Section icon="shield-checkmark" iconColor="#8B5CF6" title="5. Data Security">
      <SubHeading text="5.1 Security Measures" />
      <Bullet text="Encryption: TLS/SSL for data in transit, AES-256 for data at rest" />
      <Bullet text="Access Controls: Role-based access, multi-factor authentication" />
      <Bullet text="Firewalls: AWS WAF and network segmentation" />
      <Bullet text="Intrusion Detection: 24/7 monitoring for suspicious activity" />
      <Bullet text="Vulnerability Scanning: Regular penetration testing and code reviews" />
      <Bullet text="Secure Storage: Passwords hashed with bcrypt or Argon2" />

      <SubHeading text="5.2 Limitations" />
      <Paragraph text="No method of transmission over the Internet or electronic storage is 100% secure. While we strive to protect your information, we cannot guarantee absolute security." />

      <SubHeading text="5.3 Data Breach Notification" />
      <Paragraph text="If we discover a breach affecting your personal information, we will notify you within 30 days via email and through the Platform." />
    </Section>

    {/* 6. Data Retention */}
    <Section icon="time" iconColor="#8B5CF6" title="6. Data Retention">
      <SubHeading text="6.1 Retention Periods" />
      <Bullet text="Account Information: Duration of account + 7 years (regulatory compliance)" />
      <Bullet text="Trading Records: 7 years (SEC Rule 17a-3)" />
      <Bullet text="Communications: 3 years or as legally required" />
      <Bullet text="Marketing Data: Until you opt out" />
      <Bullet text="Analytics Data: 13 months (industry standard)" />

      <SubHeading text="6.2 Deletion Requests" />
      <Paragraph text="You may request deletion of your data subject to legal retention requirements. We will comply within 30 days where legally permitted." />
    </Section>

    {/* 7. Your Privacy Rights */}
    <Section icon="person-circle" iconColor="#8B5CF6" title="7. Your Privacy Rights">
      <SubHeading text="7.1 Access and Portability" />
      <Bullet text="Access your personal information" />
      <Bullet text="Request a copy in portable format" />
      <Bullet text="Understand how your data is used" />

      <SubHeading text="7.2 Correction" />
      <Paragraph text="You may correct inaccurate or incomplete information through your account settings or by contacting support." />

      <SubHeading text="7.3 Opt-Out" />
      <Bullet text='Marketing emails (click "Unsubscribe")' />
      <Bullet text="In-app promotional notifications (through settings)" />
      <Bullet text="Personalized recommendations (through preferences)" />
      <Bullet text="Cookies (through browser settings)" />

      <SubHeading text="7.4 Deletion" />
      <Paragraph text="You may request account deletion and associated data removal, subject to legal retention requirements." />

      <SubHeading text="7.5 Restriction of Processing" />
      <Paragraph text="You may request that we limit how we use your data." />

      <SubHeading text="7.6 CCPA/GDPR Rights (if applicable)" />
      <Paragraph text="If you're a California resident or EU resident, you have additional rights under CCPA/GDPR." />
    </Section>

    {/* 8. Cookies */}
    <Section icon="analytics" iconColor="#8B5CF6" title="8. Cookies & Tracking Technologies">
      <SubHeading text="8.1 Types of Cookies" />
      <Bullet text="Essential: Required for Platform functionality" />
      <Bullet text="Analytics: Track usage patterns (Google Analytics)" />
      <Bullet text="Marketing: Track conversions and advertising effectiveness" />
      <Bullet text="Preference: Remember your settings and preferences" />

      <SubHeading text="8.2 Cookie Management" />
      <Paragraph text="Most browsers allow you to refuse cookies or alert you when cookies are being sent. You can manage cookie preferences in your browser settings." />

      <SubHeading text="8.3 Do Not Track" />
      <Paragraph text="If your browser supports Do Not Track (DNT), we respect your preference to not be tracked for marketing purposes." />
    </Section>

    {/* 9-12 */}
    <Section icon="link" iconColor="#8B5CF6" title="9. Third-Party Links">
      <Paragraph text="The Platform may contain links to third-party websites and services. This Privacy Policy does not apply to third-party sites. We are not responsible for their privacy practices. Please review their privacy policies before providing personal information." />
    </Section>

    <Section icon="people" iconColor="#8B5CF6" title="10. Children's Privacy">
      <Paragraph text="The Platform is not intended for users under 18 years old. We do not knowingly collect personal information from children. If we discover we've collected information from a child, we will delete it immediately and notify parents." />
    </Section>

    <Section icon="airplane" iconColor="#8B5CF6" title="11. International Data Transfers">
      <Paragraph text="If you are outside the United States, your information may be transferred to, stored in, and processed in the United States. By using the Platform, you consent to such transfers." />
    </Section>

    <Section icon="refresh" iconColor="#8B5CF6" title="12. Updates to Privacy Policy">
      <Paragraph text="We may update this Privacy Policy periodically. We will notify you of material changes via email or in-app notification. Your continued use constitutes acceptance of the updated Privacy Policy." />
    </Section>

    {/* 13. Contact */}
    <Section icon="mail" iconColor="#8B5CF6" title="13. Contact Us">
      <InfoRow label="Privacy Team:" value="privacy@richesreach.com" />
      <InfoRow label="CCPA (CA):" value="ccpa@richesreach.com" />
      <InfoRow label="GDPR (EU):" value="gdpr@richesreach.com" />
      <WarningBox
        text="ACKNOWLEDGMENT: By using RichesReach, you acknowledge that you have read and agree to this Privacy Policy."
        color="#5B21B6"
        bgColor="#EDE9FE"
      />
    </Section>
  </View>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4: CYBERSECURITY POLICY
// ═══════════════════════════════════════════════════════════════════════════════

const CybersecurityTab: React.FC<{ openLink: (url: string) => void }> = ({ openLink }) => (
  <View>
    {/* 1. Executive Summary */}
    <Section icon="shield" iconColor="#EF4444" title="1. Executive Summary">
      <Paragraph text="RichesReach is committed to maintaining the highest standards of cybersecurity to protect user data, financial transactions, and platform integrity. This policy outlines our comprehensive security framework, incident response procedures, and compliance approach." />
    </Section>

    {/* 2. Security Governance */}
    <Section icon="people-circle" iconColor="#EF4444" title="2. Security Governance">
      <SubHeading text="2.1 Chief Information Security Officer (CISO)" />
      <Paragraph text="RichesReach maintains a dedicated CISO responsible for:" />
      <Bullet text="Developing and enforcing security policies" />
      <Bullet text="Conducting risk assessments" />
      <Bullet text="Managing incident response" />
      <Bullet text="Ensuring regulatory compliance" />
      <Bullet text="Training and awareness programs" />

      <SubHeading text="2.2 Security Committee" />
      <Paragraph text="A cross-functional committee meets quarterly to review:" />
      <Bullet text="Security incidents and metrics" />
      <Bullet text="Emerging threats and vulnerabilities" />
      <Bullet text="Policy updates and compliance status" />
      <Bullet text="Budget allocation for security initiatives" />

      <SubHeading text="2.3 Third-Party Risk Management" />
      <Paragraph text="All vendors and service providers undergo:" />
      <Bullet text="Security questionnaire assessment (CAIQ)" />
      <Bullet text="SOC 2 Type II certification review" />
      <Bullet text="Data handling agreement review" />
      <Bullet text="Incident notification requirements" />
    </Section>

    {/* 3. Infrastructure Security */}
    <Section icon="server" iconColor="#EF4444" title="3. Infrastructure Security">
      <SubHeading text="3.1 Cloud Architecture (AWS)" />
      <Bullet text="Amazon ECS for containerized applications" />
      <Bullet text="Amazon RDS for PostgreSQL databases" />
      <Bullet text="Amazon S3 for data storage with versioning" />
      <Bullet text="CloudFront CDN for DDoS protection" />
      <Paragraph text="Network segmentation by function with VPC isolation for production systems and principle of least privilege access." />

      <SubHeading text="3.2 Encryption" />
      <Text style={styles.miniHeading}>Data in Transit:</Text>
      <Bullet text="TLS 1.2+ for all network communications" />
      <Bullet text="HTTPS only (no HTTP endpoints)" />
      <Bullet text="SSH with public key authentication for admin access" />
      <Bullet text="End-to-end encryption for sensitive APIs" />

      <Text style={styles.miniHeading}>Data at Rest:</Text>
      <Bullet text="AES-256 encryption for all databases" />
      <Bullet text="Encrypted S3 buckets with KMS keys" />
      <Bullet text="Encrypted EBS volumes" />
      <Bullet text="Password hashing with Argon2 (not SHA1 or MD5)" />

      <SubHeading text="3.3 Access Controls" />
      <Bullet text="Multi-factor authentication (MFA) for all admin accounts" />
      <Bullet text="Role-based access control (RBAC)" />
      <Bullet text="Temporary credentials with auto-expiration" />
      <Bullet text="API key rotation every 90 days" />
      <Bullet text="No shared credentials (all auditable)" />

      <SubHeading text="3.4 Network Security" />
      <Bullet text="AWS Web Application Firewall (WAF)" />
      <Bullet text="Rate limiting to prevent brute-force attacks" />
      <Bullet text="IP whitelisting for admin access" />
      <Bullet text="DDoS mitigation via AWS Shield" />
      <Bullet text="CloudWatch monitoring for all infrastructure" />
      <Bullet text="Real-time alerting for anomalous activity" />
      <Bullet text="VPC Flow Logs for network analysis" />
    </Section>

    {/* 4. Application Security */}
    <Section icon="code-slash" iconColor="#EF4444" title="4. Application Security">
      <SubHeading text="4.1 Secure Development Lifecycle (SDLC)" />
      <Text style={styles.miniHeading}>Requirements Phase:</Text>
      <Bullet text="Security requirements documented" />
      <Bullet text="Threat modeling conducted" />
      <Bullet text="Compliance review (SOX, PCI, FINRA)" />

      <Text style={styles.miniHeading}>Development Phase:</Text>
      <Bullet text="Code reviews for all pull requests" />
      <Bullet text="Static Application Security Testing (SAST)" />
      <Bullet text="OWASP Top 10 compliance checks" />
      <Bullet text="No hard-coded credentials or API keys" />

      <Text style={styles.miniHeading}>Testing Phase:</Text>
      <Bullet text="Dynamic Application Security Testing (DAST)" />
      <Bullet text="Penetration testing by third parties (quarterly)" />
      <Bullet text="Load testing for resilience" />
      <Bullet text="Security regression tests" />

      <Text style={styles.miniHeading}>Deployment Phase:</Text>
      <Bullet text="Code signing for releases" />
      <Bullet text="Staged rollout (dev → staging → production)" />
      <Bullet text="Automated security scanning in CI/CD pipeline" />
      <Bullet text="Blue-green deployments for zero-downtime updates" />

      <SubHeading text="4.2 Vulnerability Management" />
      <Bullet text="Critical vulnerabilities fixed within 24 hours" />
      <Bullet text="High severity within 7 days" />
      <Bullet text="Medium within 30 days" />
      <Bullet text="Low within 90 days" />
      <Bullet text="Bug bounty program with Bugcrowd" />

      <SubHeading text="4.3 API Security" />
      <Bullet text="OAuth 2.0 for user authorization" />
      <Bullet text="JWT tokens with 1-hour expiration" />
      <Bullet text="Rate limiting per API key (1000 req/minute)" />
      <Bullet text="SQL injection prevention (parameterized queries)" />
      <Bullet text="XSS prevention (output encoding)" />
      <Bullet text="CSRF token validation" />
      <Bullet text="All API requests logged (sensitive data never logged)" />
    </Section>

    {/* 5. Data Protection */}
    <Section icon="lock-closed" iconColor="#EF4444" title="5. Data Protection">
      <SubHeading text="5.1 Personal Information Handling" />
      <Text style={styles.miniHeading}>Classification:</Text>
      <Bullet text="Restricted: SSN, bank account numbers, trading API keys" />
      <Bullet text="Confidential: Email, phone, address, trading history" />
      <Bullet text="Internal: Usage data, analytics, non-PII metadata" />
      <Paragraph text="Restricted data is encrypted in transit and at rest, accessed only via HTTPS, tokenized where possible, and retained minimally (30 days max for SSN after KYC)." />

      <SubHeading text="5.2 Financial Data Security" />
      <Bullet text="Bank account numbers encrypted with AES-256" />
      <Bullet text="Broker API credentials never stored in plaintext" />
      <Bullet text="OAuth tokens for broker integration (no password storage)" />
      <Bullet text="All trades logged for audit trail" />
      <Bullet text="Settlement data reconciliation daily" />
      <Bullet text="7-year retention per SEC Rule 17a-3" />

      <SubHeading text="5.3 Broker Integration Security" />
      <Bullet text="OAuth 2.0 authorization (never store passwords)" />
      <Bullet text="API credentials encrypted in database" />
      <Bullet text="Rate limiting respected per Alpaca guidelines" />
      <Bullet text="Secure order execution with confirmation" />
    </Section>

    {/* 6. Endpoint Security */}
    <Section icon="phone-portrait" iconColor="#EF4444" title="6. Endpoint Security">
      <SubHeading text="6.1 Mobile Application Security" />
      <Bullet text="No hardcoded secrets or API keys in code" />
      <Bullet text="Certificate pinning for API communication" />
      <Bullet text="Secure key storage using platform-specific keychains" />
      <Bullet text="Code obfuscation for sensitive logic" />
      <Bullet text="Remote wipe capability if device compromised" />
      <Bullet text="Biometric authentication support" />
      <Bullet text="Session timeout (15 minutes of inactivity)" />
      <Bullet text="No caching of sensitive data on device" />

      <SubHeading text="6.2 Employee Devices" />
      <Bullet text="Full-disk encryption (BitLocker/FileVault)" />
      <Bullet text="Antivirus and malware protection" />
      <Bullet text="Latest OS security patches" />
      <Bullet text="VPN for all remote access" />
      <Bullet text="Device fingerprinting and geo-fencing" />
    </Section>

    {/* 7. Incident Response */}
    <Section icon="alert-circle" iconColor="#EF4444" title="7. Incident Response">
      <SubHeading text="7.1 Incident Classification" />
      <Bullet text="Critical: Data breach, full service outage, financial impact >$100K" />
      <Bullet text="High: Partial outage, suspected attack, API unavailable" />
      <Bullet text="Medium: Minor feature issue, performance degradation" />
      <Bullet text="Low: Cosmetic issues, documentation errors" />

      <SubHeading text="7.2 Response Procedures" />
      <Bullet text="24/7 security monitoring via CloudWatch and Splunk" />
      <Bullet text="Alerts for failed login attempts (5+ in 10 minutes)" />
      <Bullet text="Critical: Immediate investigation, customer notification within 1 hour" />
      <Bullet text="High: Root cause analysis within 4 hours" />
      <Bullet text="Medium: Resolution within 24 hours" />
      <Bullet text="Customer notification if personal data affected (within 30 days per CCPA)" />
      <Bullet text="Regulatory notification if required (SEC, FINRA, state AG)" />

      <SubHeading text="7.3 Post-Incident Review" />
      <Paragraph text="Lessons learned meeting within 5 days; process improvements identified; policy updates if necessary; team training on incident prevention." />
    </Section>

    {/* 8. Business Continuity */}
    <Section icon="cloud" iconColor="#EF4444" title="8. Business Continuity & Disaster Recovery">
      <SubHeading text="8.1 Backup Strategy" />
      <Bullet text="Database backups: every 6 hours, retained for 30 days" />
      <Bullet text="Application backups: every 24 hours, retained for 7 days" />
      <Bullet text="Critical configuration: every hour, retained indefinitely" />
      <Bullet text="Backups stored in separate AWS region, encrypted at rest" />
      <Bullet text="Tested for recoverability monthly" />

      <SubHeading text="8.2 Disaster Recovery Plan" />
      <Bullet text="Recovery Time Objective (RTO): 4 hours for critical systems" />
      <Bullet text="Recovery Point Objective (RPO): 1 hour (maximum data loss)" />
      <Bullet text="DNS failover to backup region within 10 minutes" />
      <Bullet text="Database replication for near real-time recovery" />
      <Bullet text="Quarterly disaster recovery drills; annual full failover test" />
    </Section>

    {/* 9. Compliance */}
    <Section icon="ribbon" iconColor="#EF4444" title="9. Compliance">
      <SubHeading text="9.1 Regulatory Compliance" />
      <Bullet text="SEC: Rules 17a-3, 17a-4, 17a-5" />
      <Bullet text="FINRA: Rules 4512, 4513, 4530" />
      <Bullet text="FinCEN: CIP, KYC, SAR, CTR" />

      <SubHeading text="9.2 Standards and Certifications" />
      <Bullet text="ISO/IEC 27001: Target certification (in progress)" />
      <Bullet text="SOC 2 Type II: Annual audit" />
      <Bullet text="NIST Cybersecurity Framework: Implementation aligned" />
      <Bullet text="CIS Controls: Implementation of top 20 critical controls" />

      <SubHeading text="9.3 Audit and Testing" />
      <Bullet text="Annual penetration testing by third-party firm" />
      <Bullet text="Quarterly vulnerability scans (internal and external)" />
      <Bullet text="Monthly security-focused code reviews" />
      <Bullet text="Continuous monitoring: CloudWatch, Splunk, WAF logs" />
    </Section>

    {/* 10. Training */}
    <Section icon="school" iconColor="#EF4444" title="10. Training & Awareness">
      <SubHeading text="10.1 Employee Training" />
      <Bullet text="Mandatory cybersecurity awareness training on onboarding" />
      <Bullet text="Password management best practices" />
      <Bullet text="Phishing identification training" />
      <Bullet text="Annual refresher training" />
      <Bullet text="Monthly security newsletters" />
      <Bullet text="Quarterly security workshops" />
      <Bullet text="Incident simulation exercises" />

      <SubHeading text="10.2 User Education" />
      <Bullet text="Security tips in the learning module" />
      <Bullet text="Phishing email warnings" />
      <Bullet text="Password hygiene recommendations" />
      <Bullet text="Two-factor authentication encouragement" />
    </Section>

    {/* 11. Third-Party Security */}
    <Section icon="git-network" iconColor="#EF4444" title="11. Third-Party Security">
      <SubHeading text="11.1 Vendor Assessment" />
      <Bullet text="Security questionnaire assessment (CAIQ)" />
      <Bullet text="SOC 2 Type II audit report review" />
      <Bullet text="Encryption practices verification" />
      <Bullet text="Annual reassessment" />

      <SubHeading text="11.2 Data Processor Agreements" />
      <Paragraph text="All vendors sign Data Processing Agreements (DPA) including scope of processing, data security requirements, sub-processor notification, breach notification procedures, data deletion upon contract termination, and right to audit." />
    </Section>

    {/* 12. Incident Reporting */}
    <Section icon="megaphone" iconColor="#EF4444" title="12. Incident Reporting">
      <InfoRow label="Security Issues:" value="security@richesreach.com" />
      <InfoRow label="Legal/SEC:" value="legal@richesreach.com" />
      <InfoRow label="Data Breaches:" value="privacy@richesreach.com" />
      <InfoRow label="Fraud:" value="compliance@richesreach.com" />
      <Paragraph text="Responsible Disclosure Policy: No public disclosure before 30-day remediation window." />
    </Section>

    {/* 13. Policy Review */}
    <Section icon="calendar" iconColor="#EF4444" title="13. Policy Review & Updates">
      <Paragraph text="This policy is reviewed annually (minimum), following any security incident, when regulations change, and when new technologies are deployed." />
      <InfoRow label="Last Review:" value="February 5, 2026" />
      <InfoRow label="Next Review:" value="February 5, 2027" />
      <WarningBox
        text="ACKNOWLEDGMENT: All RichesReach employees must acknowledge understanding of this Cybersecurity Policy upon hire and annually thereafter."
        color="#991B1B"
        bgColor="#FEE2E2"
      />
    </Section>
  </View>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 5: PRICING & FEE AGREEMENT
// ═══════════════════════════════════════════════════════════════════════════════

const PricingTab: React.FC<{ openLink: (url: string) => void }> = ({ openLink }) => (
  <View>
    {/* 1. Subscription Tiers */}
    <Section icon="layers" iconColor="#F59E0B" title="1. Subscription Tiers">
      <SubHeading text="1.1 Free Tier — $0/Month" />
      <Text style={styles.miniHeading}>Features Included:</Text>
      <Bullet text="Basic portfolio tracking (stocks only)" />
      <Bullet text="Real-time market data" />
      <Bullet text="Simple price alerts (3 max)" />
      <Bullet text="Basic technical indicators (10 indicators)" />
      <Bullet text="Educational content (learning modules)" />
      <Bullet text="Paper trading with $100K simulation money" />
      <Bullet text="Community access (read-only)" />
      <Text style={styles.miniHeading}>Limitations:</Text>
      <Bullet text="No AI coach access" />
      <Bullet text="No options trading" />
      <Bullet text="No crypto/DeFi" />
      <Bullet text="No premium analytics" />
      <Bullet text="No advanced repair suggestions" />
      <Bullet text="Ads displayed in app" />

      <SubHeading text="1.2 Premium Tier — $19.99/Month" />
      <Text style={styles.miniHeading}>Benefits (in addition to Free features):</Text>
      <Bullet text="Unlimited price alerts" />
      <Bullet text="Advanced technical indicators (35 indicators)" />
      <Bullet text="Options trading support" />
      <Bullet text="Active Repairs with repair suggestions" />
      <Bullet text="Flight Manual educational guides" />
      <Bullet text="AI Trading Coach (basic, 5 interactions/day)" />
      <Bullet text="Basic analytics (Sharpe ratio, max drawdown)" />
      <Bullet text="Real-time Greeks analysis for options" />
      <Bullet text="Crypto portfolio tracking" />
      <Bullet text="Ad-free experience" />
      <Bullet text="Email support (24-hour response)" />
      <Bullet text="API access (limited to 100 requests/day)" />
      <Text style={styles.miniHeading}>Limitations:</Text>
      <Bullet text="No DeFi vaults" />
      <Bullet text="No HFT system access" />
      <Bullet text="No advanced AI modeling" />
      <Bullet text="No priority customer support" />
      <Bullet text="No custom strategies" />
      <Paragraph text="Billing: Monthly recurring charge on billing date. Automatic renewal unless canceled. Prorated if upgraded mid-month." />

      <SubHeading text="1.3 Pro Tier — $49.99/Month" />
      <Text style={styles.miniHeading}>Benefits (includes all Premium features plus):</Text>
      <Bullet text="Unlimited AI Coach interactions" />
      <Bullet text="HFT system access (4 strategies)" />
      <Bullet text="Advanced AI modeling and backtesting" />
      <Bullet text="DeFi vault management (yield farming)" />
      <Bullet text="Staking and yield optimization" />
      <Bullet text="Advanced repair strategies" />
      <Bullet text="Swing trading dashboard" />
      <Bullet text="Options chain analysis tools" />
      <Bullet text="Greeks modeling and simulation" />
      <Bullet text="Priority order execution (via Alpaca)" />
      <Bullet text="Priority email + phone support (2-hour response)" />
      <Bullet text="Unlimited API access" />
      <Bullet text="Custom strategy creation" />
      <Bullet text="Backtesting tools with historical data" />
      <Bullet text="Portfolio rebalancing automation" />
      <Bullet text="Tax-loss harvesting optimizer" />
      <Text style={styles.miniHeading}>Limitations:</Text>
      <Bullet text="Not available in all states (crypto features restricted)" />
      <Bullet text="HFT system requires minimum $10,000 account balance" />
      <Paragraph text="Billing: Monthly recurring charge on billing date. Automatic renewal unless canceled. Prorated if downgraded mid-month." />
    </Section>

    {/* 2. Trading and Transaction Fees */}
    <Section icon="swap-horizontal" iconColor="#F59E0B" title="2. Trading & Transaction Fees">
      <SubHeading text="2.1 Stock Trading Fees" />
      <Paragraph text="Commission: FREE. RichesReach offers commission-free stock trading through Alpaca Securities LLC." />
      <Paragraph text="Payment for Order Flow (PFOF): RichesReach receives PFOF from market makers. This does NOT increase your trading costs, but may influence order routing." />

      <SubHeading text="2.2 Options Trading Fees" />
      <Paragraph text="Commission: FREE. Per-Contract Fee: $0.65 per contract (closing transaction only)." />
      <Paragraph text="Example: Buy to open 1 call contract: $0. Sell to close 1 call contract: $0.65 fee." />

      <SubHeading text="2.3 Cryptocurrency Trading Fees" />
      <Paragraph text="Spread Fee: 1-2% on buy/sell prices. No hidden fees. No deposit or withdrawal fees (except blockchain network fees for on-chain transfers). No trading commissions." />
      <Paragraph text="DeFi operations (staking, swaps) subject to network gas fees. RichesReach does not profit from gas fees. Gas fees displayed before transaction confirmation." />

      <SubHeading text="2.4 Wire and Deposit Fees" />
      <Text style={styles.miniHeading}>Deposits:</Text>
      <Bullet text="ACH transfer: FREE (1-3 business days)" />
      <Bullet text="Wire transfer: FREE (same-day)" />
      <Bullet text="Debit card: FREE (instantaneous)" />
      <Text style={styles.miniHeading}>Withdrawals:</Text>
      <Bullet text="ACH: FREE (1-3 business days)" />
      <Bullet text="Wire transfer: $0 (broker-covered)" />
      <Bullet text="Debit card: FREE (1-2 business days)" />
    </Section>

    {/* 3. DeFi and Vault Fees */}
    <Section icon="cube" iconColor="#F59E0B" title="3. DeFi & Vault Fees">
      <SubHeading text="3.1 ERC-4626 Vault Performance Fees" />
      <Paragraph text="Annual Fee: 0.5% of vault yields. Only charged on profits generated; no fee if vault loses money." />
      <Paragraph text="Example: If vault generates $1,000 in yield, $5 fee is charged and deducted automatically from vault balance." />

      <SubHeading text="3.2 Staking and Lending Fees" />
      <Bullet text="Lido (ETH Staking): RichesReach charges 0%. Lido charges 10% of staking rewards. You receive 90% of staking rewards." />
      <Bullet text="AAVE Lending: RichesReach charges 0%. AAVE protocol fees apply per lending market." />
      <Bullet text="Compound Lending: RichesReach charges 0%. Compound protocol fees apply per market." />
      <Bullet text="Intent Swaps: RichesReach routing fee 0.05% of swap amount. DEX fees apply. Total typical cost 0.3-0.35% per swap." />
    </Section>

    {/* 4. Subscription Billing */}
    <Section icon="card" iconColor="#F59E0B" title="4. Subscription Billing">
      <SubHeading text="4.1 Billing Cycle" />
      <Bullet text="Monthly: Billed on the same calendar day each month" />
      <Bullet text="First month: Pro-rated charge based on signup date" />
      <Bullet text="Renewal: Automatic renewal 30 days before expiration" />

      <SubHeading text="4.2 Payment Methods" />
      <Paragraph text="Accepted: Major credit cards, debit cards, ACH bank account (limited to 1 per account). Processed securely via Stripe. No payment information stored on RichesReach servers. Card details tokenized for recurring billing." />

      <SubHeading text="4.3 Failed Payments" />
      <Bullet text="First attempt: Immediate retry" />
      <Bullet text="Second attempt: 3 days later" />
      <Bullet text="Third attempt: 7 days later" />
      <Bullet text="After 10 days: Account downgraded to Free tier. Premium/Pro features disabled. Notification sent via email and in-app." />
      <Paragraph text="Reinstatement: Update payment method to restore service. No data loss (settings and watchlists retained)." />
    </Section>

    {/* 5. Cancellation and Refunds */}
    <Section icon="return-down-back" iconColor="#F59E0B" title="5. Cancellation & Refunds">
      <SubHeading text="5.1 Cancellation" />
      <Text style={styles.miniHeading}>How to Cancel:</Text>
      <Bullet text="In-app: Settings → Subscription → Cancel Subscription" />
      <Bullet text="Email: support@richesreach.com" />
      <Paragraph text="Cancellations processed immediately. Pro-rated refund issued if canceled within 7 days of signup; otherwise effective at end of current billing cycle. After cancellation: downgraded to Free tier. Watchlists and history preserved. Resubscribe anytime." />

      <SubHeading text="5.2 Refunds" />
      <Paragraph text="7-Day Money-Back Guarantee: Full refund if subscription canceled within 7 days. Applies to first subscription only. Processed within 5-10 business days." />
      <Paragraph text="After 7 days: No refunds for subscription fees already paid (unless otherwise applicable). Trading fees are non-refundable." />
      <Text style={styles.miniHeading}>Non-Refundable:</Text>
      <Bullet text="Unauthorized account access (your responsibility)" />
      <Bullet text="Trading losses" />
      <Bullet text="Crypto losses" />
      <Bullet text="DeFi losses" />

      <SubHeading text="5.3 Refund for Service Issues" />
      <Bullet text="Outage > 4 hours during trading hours: 1 day pro-rated refund" />
      <Bullet text="Outage > 24 hours: 1 week pro-rated refund" />
      <Bullet text="Outage > 72 hours: 1 month full refund" />
      <Bullet text="Critical bug preventing core functionality: Pro-rated refund case-by-case" />
      <Bullet text="Minor bugs: Credit toward next month" />
    </Section>

    {/* 6. Price Changes */}
    <Section icon="trending-up" iconColor="#F59E0B" title="6. Price Changes">
      <SubHeading text="6.1 Future Price Adjustments" />
      <Bullet text="30 days written notice (email + in-app)" />
      <Bullet text="Existing customers grandfathered for 1 year at current price" />
      <Bullet text="New/renewed subscriptions charged at new rate" />
      <Bullet text="Right to accept or decline new pricing (cancel without penalty)" />

      <SubHeading text="6.2 Fee Changes" />
      <Bullet text="Trading fees and spreads may vary with market conditions" />
      <Bullet text="Options per-contract fees subject to Alpaca partner changes" />
      <Bullet text="14 days notice before any fee increase" />
      <Bullet text="Vault fees subject to governance votes; notification at least 30 days before change" />
    </Section>

    {/* 7. Third-Party Fees */}
    <Section icon="git-branch" iconColor="#F59E0B" title="7. Third-Party Fees">
      <Paragraph text="RichesReach is not responsible for: broker fees charged by Alpaca Securities LLC, payment processor fees, blockchain network fees (gas), DEX protocol fees, or bank fees for ACH transfers. Your broker or bank may charge additional fees. Review their terms separately." />
    </Section>

    {/* 8. Tax Reporting */}
    <Section icon="receipt" iconColor="#F59E0B" title="8. Tax Reporting">
      <SubHeading text="8.1 Your Responsibility" />
      <Bullet text="Calculating taxable gains/losses" />
      <Bullet text="Reporting all cryptocurrency transactions" />
      <Bullet text="Calculating wash sale implications" />
      <Bullet text="Estimating quarterly tax payments" />
      <Bullet text="Filing all required tax forms" />

      <SubHeading text="8.2 Tax Documents Provided" />
      <Bullet text="Annual 1099-B forms for stocks and options (if applicable)" />
      <Bullet text="Crypto transaction export (CSV)" />
      <Bullet text="Tax-loss harvest summary" />
      <Bullet text="Downloadable transaction history" />
      <WarningBox text="Note: RichesReach is not a tax advisor. Consult a CPA or tax professional for tax guidance." />
    </Section>

    {/* 9. Account Suspension */}
    <Section icon="ban" iconColor="#F59E0B" title="9. Account Suspension for Non-Payment">
      <SubHeading text="9.1 Suspension Policy" />
      <Bullet text="Payment fails and remains unpaid for 30 days" />
      <Bullet text="Subscription charged to invalid payment method" />
      <Bullet text="Fraudulent billing detected" />

      <SubHeading text="9.2 Reinstatement" />
      <Bullet text="Update payment method to restore Premium/Pro features" />
      <Bullet text="Past-due amount charged when service restored" />
      <Bullet text="No penalty fees" />
      <Bullet text="Full access restored within 1 hour" />
    </Section>

    {/* 10. Disputes */}
    <Section icon="chatbox-ellipses" iconColor="#F59E0B" title="10. Disputes & Chargebacks">
      <SubHeading text="10.1 Billing Disputes" />
      <Bullet text="Contact support: billing@richesreach.com" />
      <Bullet text="Provide details of dispute" />
      <Bullet text="Investigation within 5 business days" />
      <Bullet text="Resolution or refund within 10 business days" />

      <SubHeading text="10.2 Chargebacks" />
      <Paragraph text="If you dispute a charge with your credit card company, your RichesReach account may be permanently suspended, access to historical data restricted, future accounts may require pre-payment, and collection action may be pursued." />
      <WarningBox text="Prevention: Contact support first before filing a chargeback." />
    </Section>

    {/* 11. Agreement Acknowledgment */}
    <Section icon="checkmark-done" iconColor="#F59E0B" title="11. Agreement Acknowledgment">
      <Paragraph text="By using RichesReach's paid services, you acknowledge that you:" />
      <Bullet text="Have read and understand this Pricing & Fee Agreement" />
      <Bullet text="Agree to all fees outlined in this document" />
      <Bullet text="Authorize recurring billing to your selected payment method" />
      <Bullet text="Understand the refund policy (7 days money-back guarantee)" />
      <Bullet text="Accept that trading fees may vary with market conditions" />
    </Section>

    {/* 12. Contact */}
    <Section icon="mail" iconColor="#F59E0B" title="12. Contact Us">
      <InfoRow label="Billing:" value="billing@richesreach.com" />
      <InfoRow label="Pricing:" value="pricing@richesreach.com" />
      <InfoRow label="Refunds:" value="refunds@richesreach.com" />
      <InfoRow label="Hours:" value="Mon-Fri, 9 AM - 5 PM ET" />
    </Section>
  </View>
);

// ─── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F6FA',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1C1C1E',
    flex: 1,
  },
  closeButton: {
    padding: 4,
  },

  // Tab Bar
  tabBar: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    maxHeight: 56,
  },
  tabBarContent: {
    paddingHorizontal: 12,
    alignItems: 'center',
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginHorizontal: 2,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#007AFF',
  },
  tabLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#9CA3AF',
    marginLeft: 6,
  },

  // Sections
  section: {
    backgroundColor: '#FFFFFF',
    marginTop: 16,
    padding: 20,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#E5E5EA',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginLeft: 8,
    flex: 1,
  },

  // Disclosure Box
  disclosureBox: {
    backgroundColor: '#F5F6FA',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  disclosureTextBold: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
    lineHeight: 22,
  },
  disclosureText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },

  // Info Rows
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F6FA',
  },
  infoLabel: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 14,
    color: '#1C1C1E',
    fontWeight: '600',
    flexShrink: 1,
    textAlign: 'right',
  },

  // Links
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#F5F6FA',
    borderRadius: 8,
    marginTop: 8,
  },
  linkText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },

  // Warning
  warningBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF3C7',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  warningText: {
    fontSize: 13,
    color: '#92400E',
    marginLeft: 8,
    flex: 1,
    lineHeight: 18,
  },

  // Bullets
  bulletPoint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  bullet: {
    fontSize: 16,
    color: '#6B7280',
    marginRight: 8,
    marginTop: 2,
  },
  bulletText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    flex: 1,
  },

  // Text
  subHeading: {
    fontSize: 15,
    fontWeight: '700',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  miniHeading: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4B5563',
    marginTop: 8,
    marginBottom: 6,
  },
  paragraph: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 8,
  },

  // Footer
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginBottom: 4,
  },
});

export default LicensingDisclosureScreen;
