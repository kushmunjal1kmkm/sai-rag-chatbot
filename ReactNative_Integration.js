// React Native Integration Code for SAI RAG Chatbot
// Copy this to your friend's React Native app

import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Alert } from 'react-native';

const ChatbotScreen = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // REPLACE WITH YOUR ACTUAL RENDER URL AFTER DEPLOYMENT
  const API_BASE_URL = 'https://your-app-name.onrender.com';

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = { type: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const botMessage = { 
        type: 'bot', 
        content: data.answer || 'Sorry, I could not process your request.'
      };
      
      setChatHistory(prev => [...prev, botMessage]);
      
    } catch (error) {
      console.error('Error:', error);
      Alert.alert('Error', 'Failed to get response from chatbot');
    } finally {
      setLoading(false);
      setMessage('');
    }
  };

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const data = await response.json();
      Alert.alert('Health Check', `Status: ${data.status}`);
    } catch (error) {
      Alert.alert('Error', 'API is not reachable');
    }
  };

  return (
    <View style={{ flex: 1, padding: 20, backgroundColor: '#f5f5f5' }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 }}>
        SAI Sports Chatbot
      </Text>
      
      {/* Health Check Button */}
      <TouchableOpacity 
        onPress={checkHealth}
        style={{ backgroundColor: '#007bff', padding: 10, borderRadius: 5, marginBottom: 10 }}
      >
        <Text style={{ color: 'white', textAlign: 'center' }}>Test Connection</Text>
      </TouchableOpacity>

      {/* Chat History */}
      <ScrollView style={{ flex: 1, marginBottom: 20 }}>
        {chatHistory.map((chat, index) => (
          <View key={index} style={{
            backgroundColor: chat.type === 'user' ? '#007bff' : '#e9ecef',
            padding: 10,
            marginVertical: 5,
            borderRadius: 10,
            alignSelf: chat.type === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%'
          }}>
            <Text style={{ color: chat.type === 'user' ? 'white' : 'black' }}>
              {chat.content}
            </Text>
          </View>
        ))}
        {loading && (
          <Text style={{ textAlign: 'center', fontStyle: 'italic', color: '#666' }}>
            AI is thinking...
          </Text>
        )}
      </ScrollView>

      {/* Input Section */}
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <TextInput
          style={{
            flex: 1,
            borderWidth: 1,
            borderColor: '#ddd',
            borderRadius: 20,
            paddingHorizontal: 15,
            paddingVertical: 10,
            marginRight: 10,
            backgroundColor: 'white'
          }}
          placeholder="Ask about sports, training, nutrition..."
          value={message}
          onChangeText={setMessage}
          multiline
        />
        <TouchableOpacity
          onPress={sendMessage}
          disabled={loading}
          style={{
            backgroundColor: loading ? '#ccc' : '#28a745',
            paddingHorizontal: 20,
            paddingVertical: 10,
            borderRadius: 20
          }}
        >
          <Text style={{ color: 'white', fontWeight: 'bold' }}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ChatbotScreen;

/* 
DEPLOYMENT STEPS FOR YOUR FRIEND:

1. Install dependencies:
   npm install react-native-vector-icons (if using icons)

2. Replace API_BASE_URL with your actual Render deployment URL

3. Add this screen to your navigation:
   import ChatbotScreen from './ChatbotScreen';

4. Test connection first with the "Test Connection" button

5. For iOS: Add App Transport Security settings if needed:
   Add to Info.plist:
   <key>NSAppTransportSecurity</key>
   <dict>
     <key>NSAllowsArbitraryLoads</key>
     <true/>
   </dict>

6. For Android: Add network security config if needed:
   Add to android/app/src/main/res/xml/network_security_config.xml:
   <?xml version="1.0" encoding="utf-8"?>
   <network-security-config>
     <domain-config cleartextTrafficPermitted="true">
       <domain includeSubdomains="true">your-app-name.onrender.com</domain>
     </domain-config>
   </network-security-config>
*/