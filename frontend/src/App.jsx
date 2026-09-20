import coupons from "../../zepto_coupons.json";
import "./App.css";

const App = () => {
  return (
    <div className="coupon-grid">
      {coupons.map(({ coupon_code: code, title, state, unlock_message: unlockMsg, description: desc }) => {
        const isLocked = state === "Locked";

        return (
          <div key={code} className={`coupon-card ${isLocked ? "locked" : ""}`}>
            <span className="coupon-state">{isLocked ? "🔒 Locked" : `✅ ${state}`}</span>
            <h3 className="coupon-title">{title}</h3>
            <p className="coupon-desc">{desc}</p>

            {isLocked && unlockMsg && <p className="coupon-unlock">{unlockMsg}</p>}

            <div className="coupon-code">{code}</div>
          </div>
        );
      })}
    </div>
  );
};

export default App;