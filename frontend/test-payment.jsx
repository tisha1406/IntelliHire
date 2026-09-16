import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import Payment from './src/pages/company/subscription/Payment.jsx';
import { AuthContext } from './src/context/AuthContext.jsx';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><html><body><div id="root"></div></body></html>');
global.window = dom.window;
global.document = dom.window.document;


const mockCompanyProfile = {
  subscription: {
    status: 'pending_payment'
  }
};

const TestProvider = ({ children }) => (
  <AuthContext.Provider value={{ companyProfile: mockCompanyProfile, refreshUser: () => {}, setCompanyProfile: () => {} }}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </AuthContext.Provider>
);

try {
  console.log("Rendering Payment.jsx...");
  const root = createRoot(document.getElementById('root'));
  root.render(<TestProvider><Payment /></TestProvider>);
  
  setTimeout(() => {
    console.log("Render completed without throwing synchronously.");
    console.log("Root innerHTML length:", document.getElementById('root').innerHTML.length);
  }, 1000);
} catch (err) {
  console.error("RENDER ERROR:", err);
}
