import React from "react";
import { Icon } from "@aws-amplify/ui-react";

import {
  MdDashboard,
  MdModeEditOutline,
  MdAccountBox,
  MdOutlineTableChart,
} from "react-icons/md";

export const baseConfig = {
  projectLink: "/", // GitHub link in the navbar
  docsRepositoryBase: "", // base URL for the docs repository
  titleSuffix: "",
  search: true,
  header: true,
  headerText: "WRF-Platform",
  footer: true,
  footerText: (
    <>
      <span>
        © MIT {new Date().getFullYear()}, Made with ❤️ by {""}
        <a href="https://github.com/mrtzdev" target="_blank" rel="noreferrer">
          Mrtzdev
        </a>
      </span>
    </>
  ),

  logo: (
    <>
      <img
        src={"/assets/logo1.jpg"}
        alt="logo11"
        width="30"
        height="22"
      />
    </>
  ),
};

/// Navigation sidebar
export const appNavs = [
  {
    eventKey: "dashboard",
    icon: <Icon as={MdDashboard} />,
    title: "Dashboard",
    to: "/",
  },

  {
    eventKey: "settings",
    icon: <Icon as={MdOutlineTableChart} />,
    title: "Setting",
    to: "/settings",
    children: [
      {
        eventKey: "basic-table",
        title: "Basic Table",
        to: "/tables",
      },
      {
        eventKey: "users",
        title: "Users Table",
        to: "/users-table",
      },
    ],
  },
  {
    eventKey: "forms",
    icon: <Icon as={MdModeEditOutline} />,
    title: "Forms",
    to: "/forms",
    children: [
      {
        eventKey: "form-basic",
        title: "Basic",
        to: "/forms",
      },
      {
        eventKey: "form-wizard",
        title: "Edit Form",
        to: "/edit-form",
      },
    ],
  },
  {
    eventKey: "profile",
    icon: <Icon as={MdAccountBox} />,
    title: "Profile",
    to: "/profile",
  },
];