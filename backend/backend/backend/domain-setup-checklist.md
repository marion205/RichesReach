# 🎯 Domain Setup Checklist - Track Your Progress

## ✅ Step-by-Step Checklist

### Phase 1: Domain Registration
- [ ] **Go to Route 53**: [https://console.aws.amazon.com/route53/home](https://console.aws.amazon.com/route53/home)
- [ ] **Search for domain**: `richesreach.com` (or alternative)
- [ ] **Select available domain**: Choose from options
- [ ] **Add to cart**: Click "Add to cart"
- [ ] **Review and purchase**: Complete registration (~$12/year)
- [ ] **Wait for registration**: 5-10 minutes for domain to be active

### Phase 2: DNS Configuration
- [ ] **Go to Hosted Zones**: Route 53 → Hosted zones
- [ ] **Click on your domain**: `richesreach.com`
- [ ] **Create CNAME record**:
  - Record name: `app`
  - Record type: `CNAME`
  - Value: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
  - TTL: `300`
- [ ] **Save DNS record**: Wait 5-10 minutes for propagation

### Phase 3: SSL Certificate
- [ ] **Go to Certificate Manager**: [https://console.aws.amazon.com/acm/home](https://console.aws.amazon.com/acm/home)
- [ ] **Select Region**: **US East (N. Virginia) us-east-1**
- [ ] **Click "Request a certificate"**
- [ ] **Select "Request a public certificate"**
- [ ] **Domain name**: `app.richesreach.com`
- [ ] **Validation method**: **DNS validation**
- [ ] **Click "Request"**
- [ ] **Copy CNAME record** from certificate details
- [ ] **Add validation CNAME** to Route 53
- [ ] **Wait for certificate**: Status "Pending validation" → "Issued"
- [ ] **Copy Certificate ARN**: Save for next step

### Phase 4: HTTPS Deployment
- [ ] **Run HTTPS setup script**:
  ```bash
  ./setup-https-listener.sh arn:aws:acm:us-east-1:498606688292:certificate/NEW-CERT-ID
  ```
- [ ] **Wait for deployment**: 2-3 minutes
- [ ] **Test HTTPS endpoint**: `curl https://app.richesreach.com/health/`

### Phase 5: Mobile App Update
- [ ] **Run mobile app update script**:
  ```bash
  ./update-mobile-app-custom-domain.sh app.richesreach.com
  ```
- [ ] **Verify configuration**: Check updated files
- [ ] **Test mobile app**: Verify all endpoints work

### Phase 6: Final Testing
- [ ] **Test all HTTPS endpoints**:
  - `https://app.richesreach.com/`
  - `https://app.richesreach.com/health/`
  - `https://app.richesreach.com/api/ai-status`
  - `https://app.richesreach.com/api/ai-options/recommendations`
- [ ] **Test mobile app**: Verify HTTPS connectivity
- [ ] **Verify SSL certificate**: Check browser security
- [ ] **Test WebSocket**: Verify WSS connection

## 🎯 Expected Timeline
- **Domain Registration**: 5-10 minutes
- **DNS Configuration**: 5-10 minutes
- **SSL Certificate**: 10-20 minutes
- **HTTPS Deployment**: 2-3 minutes
- **Mobile App Update**: 1-2 minutes
- **Testing**: 5-10 minutes
- **Total**: 30-55 minutes

## 💰 Cost Summary
- **Domain Registration**: ~$12/year
- **Route 53 Hosted Zone**: $0.50/month
- **SSL Certificate**: FREE
- **Total Annual Cost**: ~$18/year

## 🚨 Troubleshooting
- **Domain not resolving**: Wait 10-15 minutes for DNS propagation
- **Certificate not issuing**: Check DNS validation records
- **HTTPS not working**: Verify certificate is in us-east-1 region
- **Mobile app errors**: Check custom domain configuration

## 📞 Support
- **AWS Documentation**: [Route 53 User Guide](https://docs.aws.amazon.com/route53/)
- **ACM Documentation**: [Certificate Manager User Guide](https://docs.aws.amazon.com/acm/)
- **AWS Support**: Available with support plan

## 🎉 Success Criteria
- [ ] **Custom domain resolves**: `app.richesreach.com` works
- [ ] **HTTPS is working**: Green lock in browser
- [ ] **All API endpoints**: Respond correctly
- [ ] **Mobile app**: Connects successfully
- [ ] **SSL certificate**: Valid and trusted

**Check off each item as you complete it!** ✅
