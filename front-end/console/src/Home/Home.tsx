import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import "@aws-amplify/ui-react/styles.css";
//import "./App.css";
import { ThemeProvider } from "@aws-amplify/ui-react";
import theme from "./theme";

import Layout from "../Components/Layout";
import Dashboard from "../Pages/dashboard";
import Profile from "../Pages/profile";
import Settings from "../Pages/settings";
import UsersTable from "../Pages/usersAdmin/UsersTablePage";
import DomainDetail from "../Pages/domainDetail";
import DomainCreate from "../Pages/domainCreate";

import { fetchAuthSession } from 'aws-amplify/auth'

export function Home() {
   
  const getToken = async () => {
 
    let authToken = (await fetchAuthSession()).tokens?.idToken?.toString();

    return authToken;
  };
  
  
  return (
    <ThemeProvider theme={theme}>
      <div>
        {/* Routes nest inside one another. Nested route paths build upon
            parent route paths, and nested route elements render inside
            parent route elements. See the note about <Outlet> below. */}
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="domain/:id" element={<DomainDetail getToken={getToken}/>} />
            <Route path="domain" element={<DomainCreate getToken={getToken}/>} />
            <Route path="settings" element={<Settings getToken={getToken}/>} />
            <Route path="users-table" element={<UsersTable />} />
            <Route path="profile" element={<Profile />} />

            {/* Using path="*"" means "match anything", so this route
                acts like a catch-all for URLs that we don't have explicit
                routes for. */}
            <Route path="*" element={<NoMatch />} />
          </Route>
        </Routes>
      </div>
    </ThemeProvider>
  );
}

function NoMatch() {
  return (
    <div>
      <h2>Nothing to see here!</h2>
      <p>
        <Link to="/">Go to the home page</Link>
      </p>
    </div>
  );
}
