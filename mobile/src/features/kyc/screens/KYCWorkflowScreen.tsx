import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert,
  ActivityIndicator, SafeAreaView, Modal, Image, Dimensions
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

// GraphQL Queries and Mutations
const INITIATE_KYC_WORKFLOW = gql`
  mutation InitiateKycWorkflow($workflowType: String!) {
    initiateKycWorkflow(workflowType: $workflowType) {
      success
      message
      workflow {
        userId
        workflowType
        status
        stepsRequired
        currentStep
        createdAt
        estimatedCompletion
      }
    }
  }
`;

const CREATE_BROKERAGE_ACCOUNT = gql`
  mutation CreateBrokerageAccount($kycData: JSONString!) {
    createBrokerageAccount(kycData: $kycData) {
      success
      message
      accountId
      status
    }
  }
`;

const UPLOAD_KYC_DOCUMENT = gql`
  mutation UploadKycDocument($accountId: String!, $documentType: String!, $content: String!, $contentType: String!) {
    uploadKycDocument(accountId: $accountId, documentType: $documentType, content: $content, contentType: $contentType) {
      success
      message
      documentId
    }
  }
`;

const UPDATE_KYC_STEP = gql`
  mutation UpdateKycStep($step: Int!, $status: String!, $data: JSONString) {
    updateKycStep(step: $step, status: $status, data: $data) {
      success
      message
    }
  }
`;

const COMPLETE_KYC_WORKFLOW = gql`
  mutation CompleteKycWorkflow($workflowType: String!) {
    completeKycWorkflow(workflowType: $workflowType) {
      success
      message
      nextSteps
    }
  }
`;

// Constants
const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
  green: '#22C55E',
  red: '#EF4444',
  amber: '#F59E0B',
  blueSoft: '#E8F1FF',
  successSoft: '#EAFBF1',
  dangerSoft: '#FEECEC',
  warningSoft: '#FEF3C7',
  shadow: 'rgba(16,24,40,0.08)',
};

interface KYCStep {
  step: number;
  name: string;
  required: boolean;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  completedAt?: string;
}

interface KYCWorkflowScreenProps {
  navigation: any;
  route: {
    params: {
      workflowType: 'brokerage' | 'crypto';
    };
  };
}

const KYCWorkflowScreen: React.FC<KYCWorkflowScreenProps> = ({ navigation, route }) => {
  const { workflowType } = route.params;
  const [currentStep, setCurrentStep] = useState(1);
  const [workflowStatus, setWorkflowStatus] = useState<'INITIATED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'>('INITIATED');
  const [kycData, setKycData] = useState<any>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [selectedDocumentType, setSelectedDocumentType] = useState<string>('');

  // Mutations
  const [initiateKycWorkflow] = useMutation(INITIATE_KYC_WORKFLOW);
  const [createBrokerageAccount] = useMutation(CREATE_BROKERAGE_ACCOUNT);
  const [uploadKycDocument] = useMutation(UPLOAD_KYC_DOCUMENT);
  const [updateKycStep] = useMutation(UPDATE_KYC_STEP);
  const [completeKycWorkflow] = useMutation(COMPLETE_KYC_WORKFLOW);

  // KYC Steps based on workflow type
  const getKYCSteps = (): KYCStep[] => {
    if (workflowType === 'brokerage') {
      return [
        { step: 1, name: 'Personal Information', required: true, status: 'PENDING' },
        { step: 2, name: 'Identity Verification', required: true, status: 'PENDING' },
        { step: 3, name: 'Address Verification', required: true, status: 'PENDING' },
        { step: 4, name: 'Tax Information', required: true, status: 'PENDING' },
        { step: 5, name: 'Disclosures', required: true, status: 'PENDING' },
        { step: 6, name: 'Document Upload', required: true, status: 'PENDING' },
        { step: 7, name: 'Review & Approval', required: true, status: 'PENDING' },
      ];
    } else {
      return [
        { step: 1, name: 'State Eligibility', required: true, status: 'PENDING' },
        { step: 2, name: 'Identity Verification', required: true, status: 'PENDING' },
        { step: 3, name: 'Crypto Disclosures', required: true, status: 'PENDING' },
        { step: 4, name: 'Document Upload', required: true, status: 'PENDING' },
        { step: 5, name: 'Review & Approval', required: true, status: 'PENDING' },
      ];
    }
  };

  const [steps, setSteps] = useState<KYCStep[]>(getKYCSteps());

  // Initialize workflow
  useEffect(() => {
    initializeWorkflow();
  }, []);

  const initializeWorkflow = async () => {
    setIsLoading(true);
    try {
      const result = await initiateKycWorkflow({
        variables: { workflowType }
      });

      if (result.data?.initiateKycWorkflow?.success) {
        setWorkflowStatus('IN_PROGRESS');
        const workflow = result.data.initiateKycWorkflow.workflow;
        setCurrentStep(workflow.currentStep);
      } else {
        Alert.alert('Error', 'Failed to initialize KYC workflow');
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to initialize KYC workflow');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepComplete = async (stepNumber: number, stepData: any) => {
    setIsLoading(true);
    try {
      // Update step status
      const updatedSteps = steps.map(step => 
        step.step === stepNumber 
          ? { ...step, status: 'COMPLETED' as const, completedAt: new Date().toISOString() }
          : step
      );
      setSteps(updatedSteps);

      // Update step in backend
      await updateKycStep({
        variables: {
          step: stepNumber,
          status: 'COMPLETED',
          data: stepData
        }
      });

      // Move to next step
      if (stepNumber < steps.length) {
        setCurrentStep(stepNumber + 1);
      } else {
        // All steps completed
        await completeWorkflow();
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to complete step');
    } finally {
      setIsLoading(false);
    }
  };

  const completeWorkflow = async () => {
    try {
      const result = await completeKycWorkflow({
        variables: { workflowType }
      });

      if (result.data?.completeKycWorkflow?.success) {
        setWorkflowStatus('COMPLETED');
        Alert.alert(
          'KYC Complete!',
          'Your KYC verification has been submitted for review. You will receive an email notification within 1-2 business days.',
          [
            { text: 'OK', onPress: () => navigation.goBack() }
          ]
        );
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to complete workflow');
    }
  };

  const renderStepContent = () => {
    const currentStepData = steps.find(s => s.step === currentStep);
    if (!currentStepData) return null;

    switch (currentStep) {
      case 1:
        return <PersonalInfoStep onComplete={(data) => handleStepComplete(1, data)} />;
      case 2:
        return <IdentityVerificationStep onComplete={(data) => handleStepComplete(2, data)} />;
      case 3:
        return <AddressVerificationStep onComplete={(data) => handleStepComplete(3, data)} />;
      case 4:
        return <TaxInfoStep onComplete={(data) => handleStepComplete(4, data)} />;
      case 5:
        return <DisclosuresStep onComplete={(data) => handleStepComplete(5, data)} />;
      case 6:
        return <DocumentUploadStep onComplete={(data) => handleStepComplete(6, data)} />;
      case 7:
        return <ReviewStep onComplete={(data) => handleStepComplete(7, data)} />;
      default:
        return null;
    }
  };

  const renderProgressBar = () => {
    const completedSteps = steps.filter(s => s.status === 'COMPLETED').length;
    const progress = (completedSteps / steps.length) * 100;

    return (
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>
        <Text style={styles.progressText}>
          Step {currentStep} of {steps.length} • {Math.round(progress)}% Complete
        </Text>
      </View>
    );
  };

  const renderStepIndicator = () => {
    return (
      <View style={styles.stepIndicator}>
        {steps.map((step, index) => (
          <View key={step.step} style={styles.stepItem}>
            <View style={[
              styles.stepCircle,
              step.status === 'COMPLETED' && styles.stepCircleCompleted,
              step.status === 'IN_PROGRESS' && styles.stepCircleActive,
              currentStep === step.step && styles.stepCircleCurrent
            ]}>
              {step.status === 'COMPLETED' ? (
                <Icon name="check" size={16} color="#fff" />
              ) : (
                <Text style={[
                  styles.stepNumber,
                  (step.status === 'IN_PROGRESS' || currentStep === step.step) && styles.stepNumberActive
                ]}>
                  {step.step}
                </Text>
              )}
            </View>
            <Text style={[
              styles.stepLabel,
              (step.status === 'IN_PROGRESS' || currentStep === step.step) && styles.stepLabelActive
            ]}>
              {step.name}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  if (isLoading && workflowStatus === 'INITIATED') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={C.primary} />
          <Text style={styles.loadingText}>Initializing KYC workflow...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-left" size={24} color={C.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {workflowType === 'brokerage' ? 'Brokerage Account' : 'Crypto Account'} KYC
        </Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Progress Bar */}
        {renderProgressBar()}

        {/* Step Indicator */}
        {renderStepIndicator()}

        {/* Current Step Content */}
        <View style={styles.stepContent}>
          {renderStepContent()}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// Step Components
const PersonalInfoStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    ssn: '',
    citizenship: 'USA',
    isUSCitizen: true,
    isUSResident: true,
  });

  const handleSubmit = () => {
    if (!formData.firstName || !formData.lastName || !formData.email || !formData.phone) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }
    onComplete(formData);
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Personal Information</Text>
      <Text style={styles.stepDescription}>
        Please provide your personal information for identity verification.
      </Text>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>First Name *</Text>
          <TextInput
            style={styles.input}
            value={formData.firstName}
            onChangeText={(text) => setFormData({ ...formData, firstName: text })}
            placeholder="Enter your first name"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Last Name *</Text>
          <TextInput
            style={styles.input}
            value={formData.lastName}
            onChangeText={(text) => setFormData({ ...formData, lastName: text })}
            placeholder="Enter your last name"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Email Address *</Text>
          <TextInput
            style={styles.input}
            value={formData.email}
            onChangeText={(text) => setFormData({ ...formData, email: text })}
            placeholder="Enter your email"
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Phone Number *</Text>
          <TextInput
            style={styles.input}
            value={formData.phone}
            onChangeText={(text) => setFormData({ ...formData, phone: text })}
            placeholder="(555) 123-4567"
            keyboardType="phone-pad"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Date of Birth *</Text>
          <TextInput
            style={styles.input}
            value={formData.dateOfBirth}
            onChangeText={(text) => setFormData({ ...formData, dateOfBirth: text })}
            placeholder="MM/DD/YYYY"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>SSN (Last 4 digits) *</Text>
          <TextInput
            style={styles.input}
            value={formData.ssn}
            onChangeText={(text) => setFormData({ ...formData, ssn: text })}
            placeholder="1234"
            keyboardType="numeric"
            maxLength={4}
            secureTextEntry
          />
        </View>
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
};

const IdentityVerificationStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const handleSubmit = () => {
    onComplete({ verified: true });
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Identity Verification</Text>
      <Text style={styles.stepDescription}>
        We need to verify your identity using government-issued documents.
      </Text>

      <View style={styles.infoCard}>
        <Icon name="info" size={20} color={C.primary} />
        <Text style={styles.infoText}>
          You'll need a valid driver's license, passport, or state ID to complete this step.
        </Text>
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Continue to Document Upload</Text>
      </TouchableOpacity>
    </View>
  );
};

const AddressVerificationStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const [formData, setFormData] = useState({
    streetAddress: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'USA',
  });

  const handleSubmit = () => {
    if (!formData.streetAddress || !formData.city || !formData.state || !formData.zipCode) {
      Alert.alert('Error', 'Please fill in all address fields');
      return;
    }
    onComplete(formData);
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Address Verification</Text>
      <Text style={styles.stepDescription}>
        Please provide your current residential address.
      </Text>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Street Address *</Text>
          <TextInput
            style={styles.input}
            value={formData.streetAddress}
            onChangeText={(text) => setFormData({ ...formData, streetAddress: text })}
            placeholder="123 Main Street"
          />
        </View>

        <View style={styles.inputRow}>
          <View style={[styles.inputGroup, { flex: 2 }]}>
            <Text style={styles.inputLabel}>City *</Text>
            <TextInput
              style={styles.input}
              value={formData.city}
              onChangeText={(text) => setFormData({ ...formData, city: text })}
              placeholder="New York"
            />
          </View>
          <View style={[styles.inputGroup, { flex: 1, marginLeft: 12 }]}>
            <Text style={styles.inputLabel}>State *</Text>
            <TextInput
              style={styles.input}
              value={formData.state}
              onChangeText={(text) => setFormData({ ...formData, state: text })}
              placeholder="NY"
              maxLength={2}
              autoCapitalize="characters"
            />
          </View>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>ZIP Code *</Text>
          <TextInput
            style={styles.input}
            value={formData.zipCode}
            onChangeText={(text) => setFormData({ ...formData, zipCode: text })}
            placeholder="10001"
            keyboardType="numeric"
            maxLength={10}
          />
        </View>
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
};

const TaxInfoStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const [formData, setFormData] = useState({
    taxId: '',
    isUSTaxPayer: true,
    taxResidence: 'USA',
  });

  const handleSubmit = () => {
    if (!formData.taxId) {
      Alert.alert('Error', 'Please provide your tax ID');
      return;
    }
    onComplete(formData);
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Tax Information</Text>
      <Text style={styles.stepDescription}>
        We need your tax information for regulatory compliance.
      </Text>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Tax ID (SSN) *</Text>
          <TextInput
            style={styles.input}
            value={formData.taxId}
            onChangeText={(text) => setFormData({ ...formData, taxId: text })}
            placeholder="XXX-XX-XXXX"
            keyboardType="numeric"
            secureTextEntry
          />
        </View>

        <View style={styles.checkboxGroup}>
          <TouchableOpacity 
            style={styles.checkbox}
            onPress={() => setFormData({ ...formData, isUSTaxPayer: !formData.isUSTaxPayer })}
          >
            <Icon 
              name={formData.isUSTaxPayer ? "check-square" : "square"} 
              size={20} 
              color={formData.isUSTaxPayer ? C.primary : C.sub} 
            />
            <Text style={styles.checkboxText}>I am a US tax payer</Text>
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
};

const DisclosuresStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const [disclosures, setDisclosures] = useState({
    isControlPerson: false,
    isAffiliated: false,
    isPoliticallyExposed: false,
    agreedToTerms: false,
  });

  const handleSubmit = () => {
    if (!disclosures.agreedToTerms) {
      Alert.alert('Error', 'You must agree to the terms and conditions');
      return;
    }
    onComplete(disclosures);
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Disclosures</Text>
      <Text style={styles.stepDescription}>
        Please answer the following questions for regulatory compliance.
      </Text>

      <View style={styles.form}>
        <View style={styles.checkboxGroup}>
          <TouchableOpacity 
            style={styles.checkbox}
            onPress={() => setDisclosures({ ...disclosures, isControlPerson: !disclosures.isControlPerson })}
          >
            <Icon 
              name={disclosures.isControlPerson ? "check-square" : "square"} 
              size={20} 
              color={disclosures.isControlPerson ? C.primary : C.sub} 
            />
            <Text style={styles.checkboxText}>I am a control person of a publicly traded company</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.checkboxGroup}>
          <TouchableOpacity 
            style={styles.checkbox}
            onPress={() => setDisclosures({ ...disclosures, isAffiliated: !disclosures.isAffiliated })}
          >
            <Icon 
              name={disclosures.isAffiliated ? "check-square" : "square"} 
              size={20} 
              color={disclosures.isAffiliated ? C.primary : C.sub} 
            />
            <Text style={styles.checkboxText}>I am affiliated with an exchange or FINRA</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.checkboxGroup}>
          <TouchableOpacity 
            style={styles.checkbox}
            onPress={() => setDisclosures({ ...disclosures, isPoliticallyExposed: !disclosures.isPoliticallyExposed })}
          >
            <Icon 
              name={disclosures.isPoliticallyExposed ? "check-square" : "square"} 
              size={20} 
              color={disclosures.isPoliticallyExposed ? C.primary : C.sub} 
            />
            <Text style={styles.checkboxText}>I am a politically exposed person</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.checkboxGroup}>
          <TouchableOpacity 
            style={styles.checkbox}
            onPress={() => setDisclosures({ ...disclosures, agreedToTerms: !disclosures.agreedToTerms })}
          >
            <Icon 
              name={disclosures.agreedToTerms ? "check-square" : "square"} 
              size={20} 
              color={disclosures.agreedToTerms ? C.primary : C.sub} 
            />
            <Text style={styles.checkboxText}>I agree to the terms and conditions *</Text>
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
};

const DocumentUploadStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const [uploadedDocs, setUploadedDocs] = useState<string[]>([]);

  const documentTypes = [
    { type: 'IDENTITY', name: 'Identity Document', description: 'Driver\'s license, passport, or state ID' },
    { type: 'ADDRESS', name: 'Address Proof', description: 'Utility bill, bank statement, or lease agreement' },
    { type: 'BANK_STATEMENT', name: 'Bank Statement', description: 'Recent bank statement (last 3 months)' },
  ];

  const handleDocumentUpload = (docType: string) => {
    // In a real app, this would open the camera or file picker
    Alert.alert(
      'Document Upload',
      `This would open the camera to capture your ${docType.toLowerCase()} document.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Simulate Upload', 
          onPress: () => {
            setUploadedDocs([...uploadedDocs, docType]);
            Alert.alert('Success', 'Document uploaded successfully!');
          }
        }
      ]
    );
  };

  const handleSubmit = () => {
    if (uploadedDocs.length < 2) {
      Alert.alert('Error', 'Please upload at least 2 documents');
      return;
    }
    onComplete({ documents: uploadedDocs });
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Document Upload</Text>
      <Text style={styles.stepDescription}>
        Please upload the required documents for verification.
      </Text>

      <View style={styles.form}>
        {documentTypes.map((doc) => (
          <View key={doc.type} style={styles.documentCard}>
            <View style={styles.documentInfo}>
              <Text style={styles.documentName}>{doc.name}</Text>
              <Text style={styles.documentDescription}>{doc.description}</Text>
            </View>
            <TouchableOpacity 
              style={[
                styles.uploadButton,
                uploadedDocs.includes(doc.type) && styles.uploadButtonCompleted
              ]}
              onPress={() => handleDocumentUpload(doc.type)}
            >
              {uploadedDocs.includes(doc.type) ? (
                <Icon name="check" size={20} color="#fff" />
              ) : (
                <Icon name="upload" size={20} color={C.primary} />
              )}
            </TouchableOpacity>
          </View>
        ))}
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
};

const ReviewStep: React.FC<{ onComplete: (data: any) => void }> = ({ onComplete }) => {
  const handleSubmit = () => {
    Alert.alert(
      'Submit for Review',
      'Are you ready to submit your KYC application for review?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Submit', onPress: () => onComplete({ submitted: true }) }
      ]
    );
  };

  return (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Review & Submit</Text>
      <Text style={styles.stepDescription}>
        Please review your information before submitting for approval.
      </Text>

      <View style={styles.reviewCard}>
        <Icon name="check-circle" size={24} color={C.green} />
        <Text style={styles.reviewTitle}>All Information Complete</Text>
        <Text style={styles.reviewDescription}>
          Your KYC application is ready for review. You will receive an email notification within 1-2 business days.
        </Text>
      </View>

      <TouchableOpacity style={styles.continueButton} onPress={handleSubmit}>
        <Text style={styles.continueButtonText}>Submit for Review</Text>
      </TouchableOpacity>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: C.card,
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: C.text,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: C.sub,
  },
  progressContainer: {
    marginVertical: 20,
  },
  progressBar: {
    height: 8,
    backgroundColor: C.line,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: C.primary,
    borderRadius: 4,
  },
  progressText: {
    textAlign: 'center',
    marginTop: 8,
    fontSize: 14,
    color: C.sub,
    fontWeight: '600',
  },
  stepIndicator: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  stepItem: {
    alignItems: 'center',
    flex: 1,
  },
  stepCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: C.line,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  stepCircleCompleted: {
    backgroundColor: C.green,
  },
  stepCircleActive: {
    backgroundColor: C.primary,
  },
  stepCircleCurrent: {
    backgroundColor: C.primary,
  },
  stepNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: C.sub,
  },
  stepNumberActive: {
    color: '#fff',
  },
  stepLabel: {
    fontSize: 12,
    color: C.sub,
    textAlign: 'center',
    fontWeight: '500',
  },
  stepLabelActive: {
    color: C.text,
    fontWeight: '600',
  },
  stepContent: {
    marginBottom: 30,
  },
  stepContainer: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 20,
    shadowColor: C.shadow,
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: C.text,
    marginBottom: 8,
  },
  stepDescription: {
    fontSize: 16,
    color: C.sub,
    marginBottom: 24,
    lineHeight: 22,
  },
  form: {
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    color: C.text,
  },
  checkboxGroup: {
    marginBottom: 16,
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkboxText: {
    marginLeft: 12,
    fontSize: 16,
    color: C.text,
    flex: 1,
  },
  continueButton: {
    backgroundColor: C.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  continueButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: C.blueSoft,
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    alignItems: 'flex-start',
  },
  infoText: {
    marginLeft: 12,
    fontSize: 14,
    color: C.text,
    flex: 1,
    lineHeight: 20,
  },
  documentCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: C.line,
  },
  documentInfo: {
    flex: 1,
  },
  documentName: {
    fontSize: 16,
    fontWeight: '600',
    color: C.text,
    marginBottom: 4,
  },
  documentDescription: {
    fontSize: 14,
    color: C.sub,
  },
  uploadButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: C.primary,
  },
  uploadButtonCompleted: {
    backgroundColor: C.green,
    borderColor: C.green,
  },
  reviewCard: {
    backgroundColor: C.successSoft,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
  },
  reviewTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: C.text,
    marginTop: 12,
    marginBottom: 8,
  },
  reviewDescription: {
    fontSize: 14,
    color: C.sub,
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default KYCWorkflowScreen;
