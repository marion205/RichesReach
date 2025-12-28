/**
 * Licensing Disclosure Screen
 * Displays regulatory and licensing information for App Store compliance
 * Critical for Apple App Store approval (Guideline 3.1.5(viii))
 */
import React from 'react';
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

interface LicensingDisclosureScreenProps {
  onClose?: () => void;
}

const LicensingDisclosureScreen: React.FC<LicensingDisclosureScreenProps> = ({ onClose }) => {
  const openLink = (url: string) => {
    Linking.openURL(url).catch((err) => console.error('Failed to open URL:', err));
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Regulatory & Licensing Information</Text>
          {onClose && (
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          )}
        </View>

        {/* Stock Trading Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="checkmark-circle" size={24} color="#22C55E" />
            <Text style={styles.sectionTitle}>Stock Trading Services</Text>
          </View>
          
          <View style={styles.disclosureBox}>
            <Text style={styles.disclosureTextBold}>
              Securities trading is provided through Alpaca Securities LLC, a registered broker-dealer.
            </Text>
            <Text style={styles.disclosureText}>
              Alpaca Securities LLC is a member of the Financial Industry Regulatory Authority (FINRA) 
              and the Securities Investor Protection Corporation (SIPC).
            </Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Broker-Dealer:</Text>
            <Text style={styles.infoValue}>Alpaca Securities LLC</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>FINRA Member:</Text>
            <Text style={styles.infoValue}>Yes (Member #289946)</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>SIPC Protection:</Text>
            <Text style={styles.infoValue}>Yes (Up to $500,000)</Text>
          </View>

          <TouchableOpacity 
            style={styles.linkButton}
            onPress={() => openLink('https://brokercheck.finra.org/firm/summary/289946')}
          >
            <Text style={styles.linkText}>View Alpaca's FINRA BrokerCheck</Text>
            <Ionicons name="open-outline" size={16} color="#007AFF" />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.linkButton}
            onPress={() => openLink('https://www.sipc.org/for-investors/what-sipc-protects')}
          >
            <Text style={styles.linkText}>Learn About SIPC Protection</Text>
            <Ionicons name="open-outline" size={16} color="#007AFF" />
          </TouchableOpacity>

          <View style={styles.warningBox}>
            <Ionicons name="information-circle" size={20} color="#F59E0B" />
            <Text style={styles.warningText}>
              RichesReach is not affiliated with Alpaca Securities LLC. Alpaca does not endorse 
              or recommend any particular investment strategy.
            </Text>
          </View>
        </View>

        {/* Crypto Trading Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="alert-circle" size={24} color="#F59E0B" />
            <Text style={styles.sectionTitle}>Cryptocurrency Trading</Text>
          </View>
          
          <View style={styles.disclosureBox}>
            <Text style={styles.disclosureTextBold}>
              Cryptocurrency trading is currently not available.
            </Text>
            <Text style={styles.disclosureText}>
              We are working to obtain the necessary regulatory licenses to offer cryptocurrency 
              trading services. This feature will be available in the future once all regulatory 
              requirements are met.
            </Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Status:</Text>
            <Text style={styles.infoValue}>Not Available</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Reason:</Text>
            <Text style={styles.infoValue}>Regulatory Compliance</Text>
          </View>
        </View>

        {/* Investment Advice Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="school" size={24} color="#007AFF" />
            <Text style={styles.sectionTitle}>Investment Information</Text>
          </View>
          
          <View style={styles.disclosureBox}>
            <Text style={styles.disclosureTextBold}>
              Not Investment Advice
            </Text>
            <Text style={styles.disclosureText}>
              All investment information, analysis, recommendations, and educational content 
              provided by RichesReach are for educational and informational purposes only. 
              This is not investment advice, financial planning advice, or a recommendation 
              to buy or sell securities.
            </Text>
          </View>

          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              AI recommendations are based on algorithms and market data, not individual circumstances
            </Text>
          </View>
          
          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              You should consult with a qualified financial advisor before making investment decisions
            </Text>
          </View>
          
          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              Past performance does not guarantee future results
            </Text>
          </View>
          
          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              All investments carry risk of loss
            </Text>
          </View>
        </View>

        {/* Risk Disclosure Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="warning" size={24} color="#EF4444" />
            <Text style={styles.sectionTitle}>Risk Disclosure</Text>
          </View>
          
          <View style={styles.disclosureBox}>
            <Text style={styles.disclosureTextBold}>
              Trading involves substantial risk of loss.
            </Text>
            <Text style={styles.disclosureText}>
              You may lose more than your initial investment. Market conditions can change 
              rapidly and unpredictably. Only invest money you can afford to lose.
            </Text>
          </View>

          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              All investments carry risk of loss
            </Text>
          </View>
          
          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              Past performance does not guarantee future results
            </Text>
          </View>
          
          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              Market volatility can result in significant losses
            </Text>
          </View>
          
          <View style={styles.bulletPoint}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.bulletText}>
              Diversification does not guarantee profit or protect against loss
            </Text>
          </View>
        </View>

        {/* Contact Information */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="mail" size={24} color="#007AFF" />
            <Text style={styles.sectionTitle}>Contact & Support</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Support Email:</Text>
            <TouchableOpacity onPress={() => openLink('mailto:support@richesreach.com')}>
              <Text style={styles.linkTextInline}>support@richesreach.com</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Legal Email:</Text>
            <TouchableOpacity onPress={() => openLink('mailto:legal@richesreach.com')}>
              <Text style={styles.linkTextInline}>legal@richesreach.com</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Last Updated: {new Date().toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

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
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    flex: 1,
  },
  closeButton: {
    padding: 4,
  },
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
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginLeft: 8,
  },
  disclosureBox: {
    backgroundColor: '#F5F6FA',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  disclosureTextBold: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
    lineHeight: 24,
  },
  disclosureText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
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
  },
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
  linkTextInline: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
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
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#9CA3AF',
  },
});

export default LicensingDisclosureScreen;

