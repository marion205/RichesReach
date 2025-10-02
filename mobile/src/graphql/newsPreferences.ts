import { gql } from '@apollo/client';

export const GET_NEWS_PREFERENCES = gql`
  mutation GetNewsPreferences {
    getNewsPreferences {
      success
      error
      preferences {
        breakingNews
        marketNews
        companyNews
        earningsNews
        cryptoNews
        personalStocks
        quietHours
        quietStart
        quietEnd
        frequency
      }
    }
  }
`;

export const UPDATE_NEWS_PREFERENCES = gql`
  mutation UpdateNewsPreferences($preferences: NewsPreferencesInput!) {
    updateNewsPreferences(preferences: $preferences) {
      success
      error
      preferences {
        breakingNews
        marketNews
        companyNews
        earningsNews
        cryptoNews
        personalStocks
        quietHours
        quietStart
        quietEnd
        frequency
      }
    }
  }
`;

export interface NewsPreferences {
  breakingNews: boolean;
  marketNews: boolean;
  companyNews: boolean;
  earningsNews: boolean;
  cryptoNews: boolean;
  personalStocks: boolean;
  quietHours: boolean;
  quietStart: string;
  quietEnd: string;
  frequency: 'immediate' | 'hourly' | 'daily';
}

export interface GetNewsPreferencesResponse {
  getNewsPreferences: {
    success: boolean;
    error?: string;
    preferences?: NewsPreferences;
  };
}

export interface UpdateNewsPreferencesResponse {
  updateNewsPreferences: {
    success: boolean;
    error?: string;
    preferences?: NewsPreferences;
  };
}
