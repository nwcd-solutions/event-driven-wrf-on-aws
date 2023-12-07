
import React from "react";
import { Amplify } from "aws-amplify";
import {
  useAuthenticator,
} from "@aws-amplify/ui-react";
import config from "./aws-export";
import  Home  from "./Home";
import  Login  from "./Login";
import "./styles.css";
import "@aws-amplify/ui-react/styles.css";


Amplify.configure(config);


const App =() => {
  const { user } = useAuthenticator();
  
  if (user) {
    return <Home />;
  }

  return <Login />;
};

export default App;