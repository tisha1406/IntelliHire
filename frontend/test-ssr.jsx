import React from 'react';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import Payment from './src/pages/company/subscription/Payment.jsx';
import { AuthContext } from './src/context/AuthContext.jsx';

const mockCompanyProfile = {
  subscription: {
    status: 'pending_payment'
  }
};

const TestProvider = ({ children }) => (
  <AuthContext.Provider value={{ companyProfile: mockCompanyProfile, refreshUser: () => {}, setCompanyProfile: () => {} }}>
    <StaticRouter location="/company/subscription/payment">
      {children}
    </StaticRouter>
  </AuthContext.Provider>
);

try {
  console.log("Rendering Payment.jsx...");
  const html = renderToString(<TestProvider><Payment /></TestProvider>);
  console.log("Rendered successfully! HTML length:", html.length);
  if (html.length === 0) {
    console.log("HTML IS EMPTY!");
  }
} catch (err) {
  console.error("RENDER ERROR:", err);
}
