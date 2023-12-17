import React from "react";
import { Icon } from "@aws-amplify/ui-react";

import {
  MdDashboard,
  MdModeEditOutline,
  MdAccountBox,
  MdOutlineTableChart,
  MdCloudUpload
} from "react-icons/md";

export const baseConfig = {
  projectLink: "", // GitHub link in the navbar
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
    eventKey: "domainconfig",
    icon: <Icon as={MdModeEditOutline} />,
    title: "Domain Config",
    to: "/settings",
  },
  {
    eventKey: "tasksettings",
    icon: <Icon as={MdOutlineTableChart} />,
    title: "Task Setting",
    to: "/tasks",
  },
  {
    eventKey: "files",
    icon: <Icon as={MdCloudUpload} />,
    title: "Files Management",
    to: "/files",
  },


];
