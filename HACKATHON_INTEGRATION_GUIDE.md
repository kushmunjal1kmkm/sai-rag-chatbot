# React Native Integration Guide for SAI Chatbot
## ⚡ **HACKATHON SPEED SETUP** (5 minutes)

### **Step 1: Deploy Your API (2 minutes)**
1. Push your code to GitHub
2. Go to [render.com](https://render.com)
3. Connect your GitHub repo
4. Deploy with these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment Variables**: Add `GEMINI_API_KEY`

**Your API will be live at**: `https://your-app-name.onrender.com`

### **Step 2: React Native Code (3 minutes)**
Copy the `ReactNative_Integration.js` file to your friend's project.

#### **Quick Integration Steps**:

1. **Install dependencies** (if needed):
```bash
npm install react-native-vector-icons
```

2. **Replace API URL** in the code:
```javascript
const API_BASE_URL = 'https://your-actual-render-url.onrender.com';
```

3. **Add to your navigation**:
```javascript
import ChatbotScreen from './ChatbotScreen';

// In your navigation stack
<Stack.Screen name="Chatbot" component={ChatbotScreen} />
```

### **Step 3: Test Connection**
- Use the "Test Connection" button in the app
- Should return: `{"status": "healthy"}`

---

## **Available API Endpoints**

### **Main Chat Endpoint**
```
POST /ask
Body: { "question": "Your sports question here" }
Response: { "answer": "AI response", "sources": [...] }
```

### **Health Check**
```
GET /health
Response: { "status": "healthy" }
```

### **Example API Calls**

```javascript
// Basic chat
const response = await fetch(`${API_URL}/ask`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: "What is SAI?" })
});

// Health check
const health = await fetch(`${API_URL}/health`);
```

---

## **Troubleshooting**

### **Common Issues**:

1. **Network Error**: Check if API URL is correct
2. **CORS Error**: API already has CORS enabled
3. **Timeout**: Render free tier may have cold starts (30 seconds)

### **Quick Fixes**:

1. **iOS Network Issues**: Add to `Info.plist`:
```xml
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsArbitraryLoads</key>
  <true/>
</dict>
```

2. **Android Network Issues**: Add network security config

---

## **Hackathon Tips**

1. **Deploy first**, code later
2. **Test with Postman** before React Native integration
3. **Use the health endpoint** to verify connectivity
4. **Keep API URL in environment variables** for easy switching

---

## **Alternative Options**

### **Option 2: Ngrok Tunnel (Testing Only)**
If Render is slow, use ngrok for local testing:
```bash
pip install pyngrok
python main.py
# In another terminal:
ngrok http 5000
```

### **Option 3: Vercel Deployment**
- Push to GitHub
- Connect to Vercel
- Deploy as Python app

---

## **Production Checklist**

- [ ] Environment variables set in Render
- [ ] API URL updated in React Native
- [ ] CORS working for all origins
- [ ] Health endpoint responding
- [ ] Chat endpoint tested with real questions
- [ ] Error handling in place

**Estimated Total Setup Time**: 5-10 minutes
**Best for Hackathon**: Option 1 (Render deployment)