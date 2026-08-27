import { useState } from "react";
import LoginFormUI from "./loginFormUI"; 

const LoginForm = ({ onLogin }) => {
    const [username, setUsername] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
    
        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username }),
            });
    
            const data = await response.json();
    
            if (response.ok) {
                localStorage.setItem("token", data.token);
                localStorage.setItem("username", data.username);
                
                // --- FIX: Add a delay so the animation is persistent ---
                setTimeout(() => {
                    onLogin(data.token, data.username);
                }, 1500); // 1.5 seconds of "Processing" feel
                
            } else {
                setLoading(false); // Stop loading only on error
                setError(data.message || "Login failed. Try again.");
            }
        } catch (err) {
            setLoading(false);
            setError("Server unreachable.");
        }
    };

    return <LoginFormUI 
                username={username} 
                setUsername={setUsername} 
                handleLogin={handleLogin} 
                error={error} 
                loading={loading} 
            />;
};

export default LoginForm;