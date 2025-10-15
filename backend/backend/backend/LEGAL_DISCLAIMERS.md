# ⚠️ Legal Disclaimers & Terms of Service

**⚠️ Not legal advice. Have counsel review before publishing.**

## Terms of Service (Summary)

• **RichesReach provides tools** to view, supply, borrow, and manage digital assets via third-party protocols (e.g., Aave). RichesReach does not custody user assets and does not provide investment advice.

• **By connecting a wallet**, you authorize transactions from your wallet. You're responsible for safeguarding your private keys and verifying all transactions.

• **Protocol interactions** are subject to protocol rules, network congestion, and gas fees. Transactions are irreversible once broadcast.

• **Features may be geo-restricted** and require additional verification (KYC/AML). RichesReach may refuse service where prohibited.

• **RichesReach is provided "as-is"**, without warranties. To the fullest extent permitted by law, liability is limited to the maximum allowed under applicable law.

## Risk Disclosure

• **Digital assets are volatile** and can lose value rapidly. Borrowing may result in liquidation if collateral value falls.

• **Smart contracts and protocols** carry risks, including bugs, exploits, or oracle failures.

• **Past performance** (including any model metrics) does not guarantee future results.

• **You are solely responsible** for tax reporting and compliance with applicable laws.

## Privacy

• **We collect minimal data** to provide services (e.g., public wallet addresses, device info). See full Privacy Policy for details.

## USA Compliance

This service is designed for US users and complies with applicable US regulations.

---

## App Footer Links

Place these links in your app footer:

• **Terms of Service** - Link to full terms
• **Privacy Policy** - Link to privacy policy  
• **Risk Disclosure** - Link to risk disclosure

---

## Implementation in React Native

```typescript
// Add to your app footer component
const FooterLinks = () => (
  <View style={styles.footer}>
    <TouchableOpacity onPress={() => Linking.openURL('https://yourapp.com/terms')}>
      <Text style={styles.link}>Terms of Service</Text>
    </TouchableOpacity>
    <TouchableOpacity onPress={() => Linking.openURL('https://yourapp.com/privacy')}>
      <Text style={styles.link}>Privacy Policy</Text>
    </TouchableOpacity>
    <TouchableOpacity onPress={() => Linking.openURL('https://yourapp.com/risk')}>
      <Text style={styles.link}>Risk Disclosure</Text>
    </TouchableOpacity>
  </View>
);
```

---

## Next Steps

1. **Review with legal counsel** before publishing
2. **Create full legal pages** on your website
3. **Add footer links** to your mobile app
4. **Update as needed** based on legal requirements

**Remember: This is a starting template. Always consult with qualified legal counsel before publishing any terms or disclaimers.**
