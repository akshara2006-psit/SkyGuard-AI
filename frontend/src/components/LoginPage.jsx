// import React, { useEffect, useState } from "react";
// import { ShieldCheck, Activity, Eye, Cpu, Zap, LogIn } from "lucide-react";

// export default function LoginPage({ onLoginSuccess }) {
//   const [googleClientReady, setGoogleClientReady] = useState(false);
//   const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
//   const isConfigured = clientId && !clientId.includes("your-google-client-id");

//   useEffect(() => {
//     if (!isConfigured) return;

//     // Dynamically load Google Identity Services Script
//     const script = document.createElement("script");
//     script.src = "https://accounts.google.com/gsi/client";
//     script.async = true;
//     script.defer = true;
//     script.onload = () => {
//       if (window.google?.accounts?.id) {
//         window.google.accounts.id.initialize({
//           client_id: clientId,
//           callback: handleGoogleCallback,
//         });
//         window.google.accounts.id.renderButton(
//           document.getElementById("google-signin-btn"),
//           { theme: "filled_blue", size: "large", width: 280, shape: "rectangular" }
//         );
//         setGoogleClientReady(true);
//       }
//     };
//     document.body.appendChild(script);

//     return () => {
//       // Cleanup script if component unmounts
//       if (document.body.contains(script)) {
//         document.body.removeChild(script);
//       }
//     };
//   }, [clientId, isConfigured]);

//   const handleGoogleCallback = (response) => {
//     try {
//       // Parse JWT credential token from Google
//       const base64Url = response.credential.split(".")[1];
//       const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
//       const jsonPayload = decodeURIComponent(
//         atob(base64)
//           .split("")
//           .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
//           .join("")
//       );
//       const user = JSON.parse(jsonPayload);
//       onLoginSuccess({
//         name: user.name || "AWS Operator",
//         email: user.email,
//         picture: user.picture,
//         sub: user.sub,
//       });
//     } catch (e) {
//       console.error("Failed to parse Google OAuth token", e);
//     }
//   };

//   const handleDemoLogin = () => {
//     onLoginSuccess({
//       name: "Meteorological Analyst",
//       email: "operator@skyguard.ai",
//       picture: null,
//       sub: "demo-user-001",
//     });
//   };

//   return (
//     <div className="login-screen">
//       <div className="login-card">
//         <div className="login-header">
//           <div className="login-icon">
//             <ShieldCheck size={40} color="#3b82f6" />
//           </div>
//           <h1>SKYGUARD AI</h1>
//           <p className="subtitle">
//             Intelligent Real-Time Anomaly Detection for Automatic Weather Stations
//           </p>
//         </div>

//         <div className="login-pillars">
//           <div className="pillar">
//             <Activity size={20} color="#3b82f6" />
//             <span>Monitor</span>
//           </div>
//           <div className="pillar">
//             <Eye size={20} color="#10b981" />
//             <span>Detect</span>
//           </div>
//           <div className="pillar">
//             <Cpu size={20} color="#f59e0b" />
//             <span>Explain</span>
//           </div>
//           <div className="pillar">
//             <Zap size={20} color="#8b5cf6" />
//             <span>Act</span>
//           </div>
//         </div>

//         <div className="login-action-box">
//           {isConfigured ? (
//             <div id="google-signin-btn" className="google-btn-wrapper"></div>
//           ) : (
//             <div className="auth-config-notice">
//               <p className="notice-title">Google Authentication Requires OAuth Configuration</p>
//               <p className="notice-desc">
//                 Set <code>VITE_GOOGLE_CLIENT_ID</code> in <code>.env</code> to activate production Google Identity Sign-In. Use the operator sign-in below for demo and evaluation.
//               </p>
//             </div>
//           )}

//           <button className="btn btn-primary login-btn" onClick={handleDemoLogin}>
//             <LogIn size={18} />
//             <span>Sign in as Meteorological Analyst (Demo Mode)</span>
//           </button>
//         </div>

//         <div className="login-footer">
//           <p>
//             "SkyGuard AI helps ensure that weather-station observations are trustworthy
//             before they are used for forecasting, monitoring, agriculture, aviation, or disaster-management workflows."
//           </p>
//           <span className="tagline">Trust the data before you trust the forecast.</span>
//         </div>
//       </div>
//     </div>
//   );
// }

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  Activity,
  Eye,
  Cpu,
  Zap,
  LogIn,
  ArrowRight,
  CloudRain,
  Radio,
} from "lucide-react";
import "./LoginPage.css";

export default function LoginPage({ onLoginSuccess }) {
  const [googleClientReady, setGoogleClientReady] = useState(false);

  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
  const isConfigured =
    clientId && !clientId.includes("your-google-client-id");

  useEffect(() => {
    if (!isConfigured) return;

    const script = document.createElement("script");

    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;

    script.onload = () => {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleCallback,
        });

        window.google.accounts.id.renderButton(
          document.getElementById("google-signin-btn"),
          // {
          //   theme: "filled_blue",
          //   size: "large",
          //   width: 350,
          //   shape: "rectangular",
          // }
          {
  theme: "outline",
  size: "large",
  width: 350,
  shape: "rectangular",
  text: "signin_with",
  logo_alignment: "left",
}
        );

        setGoogleClientReady(true);
      }
    };

    document.body.appendChild(script);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, [clientId, isConfigured]);

  const handleGoogleCallback = (response) => {
    try {
      const base64Url = response.credential.split(".")[1];

      const base64 = base64Url
        .replace(/-/g, "+")
        .replace(/_/g, "/");

      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split("")
          .map(
            (c) =>
              "%" +
              ("00" + c.charCodeAt(0).toString(16)).slice(-2)
          )
          .join("")
      );

      const user = JSON.parse(jsonPayload);

      onLoginSuccess({
        name: user.name || "AWS Operator",
        email: user.email,
        picture: user.picture,
        sub: user.sub,
      });
    } catch (e) {
      console.error("Failed to parse Google OAuth token", e);
    }
  };

  const handleDemoLogin = () => {
    onLoginSuccess({
      name: "Meteorological Analyst",
      email: "operator@skyguard.ai",
      picture: null,
      sub: "demo-user-001",
    });
  };

  return (
    <div className="skyguard-login">

      {/* =====================================================
          LEFT HERO SECTION
      ====================================================== */}

      <section className="skyguard-hero">

        {/* Background decoration */}
        <div className="hero-glow hero-glow-one"></div>
        <div className="hero-glow hero-glow-two"></div>

        {/* Brand */}
        <div className="skyguard-brand">

          <div className="brand-shield">
            <ShieldCheck size={30} />
          </div>

          <div>
            <h2>
              SKYGUARD <span>AI</span>
            </h2>

            <p>
              Weather Intelligence Platform
            </p>
          </div>

        </div>


        {/* Main Hero */}
        <div className="hero-main">

          <div className="live-status">
            <span className="live-dot"></span>
            AI-POWERED WEATHER INTELLIGENCE
          </div>

          <h1>
            Trust the data.
            <br />

            <span>Before you trust</span>
            <br />

            the forecast.
          </h1>

          <p className="hero-text">
            SkyGuard AI continuously monitors Automatic Weather
            Stations, detects abnormal observations, explains
            suspicious patterns, and enables faster decisions
            when every second matters.
          </p>


          {/* Weather visual */}
          <div className="weather-visual">

            <div className="weather-circle">
              <CloudRain size={45} />
            </div>

            <div className="weather-line"></div>

            <div className="weather-data">

              <div>
                <span>Station Network</span>
                <strong>ACTIVE</strong>
              </div>

              <div>
                <span>AI Monitoring</span>
                <strong>LIVE</strong>
              </div>

              <div>
                <span>Data Integrity</span>
                <strong>98.7%</strong>
              </div>

            </div>

          </div>

        </div>


        {/* Four pillars */}
        <div className="skyguard-pillars">

          <Pillar
            icon={<Activity />}
            title="Monitor"
            description="Continuous observation"
            className="pillar-blue"
          />

          <Pillar
            icon={<Eye />}
            title="Detect"
            description="Find anomalies early"
            className="pillar-green"
          />

          <Pillar
            icon={<Cpu />}
            title="Explain"
            description="Understand the cause"
            className="pillar-orange"
          />

          <Pillar
            icon={<Zap />}
            title="Act"
            description="Respond with confidence"
            className="pillar-purple"
          />

        </div>


        {/* Footer */}
        <div className="hero-footer">
          <Radio size={15} />
          Real-time intelligence for safer decisions
        </div>

      </section>


      {/* =====================================================
          RIGHT LOGIN SECTION
      ====================================================== */}

      <section className="skyguard-auth">

        <div className="auth-card">

          {/* Top icon */}
          <div className="auth-icon">
            <ShieldCheck size={38} />
          </div>


          <h2>
            Welcome to <span>SkyGuard</span>
          </h2>

          <p className="auth-description">
            Secure access to your weather intelligence
            dashboard.
          </p>


          {/* Security badge */}
          <div className="security-badge">

            <div className="security-dot"></div>

            <span>
              Secure authentication
            </span>

          </div>


          <div className="auth-divider"></div>


          <p className="continue-label">
            Continue with
          </p>


          {/* Google authentication */}
          {isConfigured ? (

            // <div className="google-container">

            //   <div
            //     id="google-signin-btn"
            //     className="google-signin"
            //   ></div>

            // </div>
            <div className="google-container">
  <div id="google-signin-btn"></div>
</div>

          ) : (

            <div className="auth-config-notice">

              <strong>
                Google Sign-In is not configured
              </strong>

              <p>
                Add <code>VITE_GOOGLE_CLIENT_ID</code> to
                your <code>.env</code> file to enable
                Google authentication.
              </p>

            </div>

          )}


          {/* OR */}
          <div className="auth-or">

            <span></span>

            <p>OR</p>

            <span></span>

          </div>


          {/* Demo login */}
          <button
            className="demo-login"
            onClick={handleDemoLogin}
          >

            <div className="demo-icon">
              <LogIn size={20} />
            </div>

            <div className="demo-text">

              <strong>
                Continue in Demo Mode
              </strong>

              <small>
                Explore the analyst dashboard
              </small>

            </div>

            <ArrowRight size={20} />

          </button>


          {/* Demo notice */}
          <div className="demo-notice">

            <ShieldCheck size={22} />

            <div>
              <strong>
                Evaluation access
              </strong>

              <p>
                Demo Mode provides full access to
                SkyGuard AI features without requiring
                a Google account.
              </p>
            </div>

          </div>


          {/* Bottom */}
          <div className="auth-footer">

            <span></span>

            <p>
              <ShieldCheck size={14} />
              Your data. Your decisions. Your safety.
            </p>

            <span></span>

          </div>

        </div>

      </section>

    </div>
  );
}


/* ============================================================
   PILLAR COMPONENT
============================================================ */

function Pillar({
  icon,
  title,
  description,
  className,
}) {
  return (
    <div className={`skyguard-pillar ${className}`}>

      <div className="pillar-icon">
        {icon}
      </div>

      <div>
        <strong>{title}</strong>

        <p>{description}</p>
      </div>

    </div>
  );
}