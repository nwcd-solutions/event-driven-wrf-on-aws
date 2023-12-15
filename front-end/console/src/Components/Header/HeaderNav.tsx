import React from "react";
import { Menu, MenuItem, MenuButton, Link } from "@aws-amplify/ui-react";
import { useNavigate } from "react-router-dom";
import { AiFillGithub } from "react-icons/ai";
import { baseConfig } from "../../config";
import { useAuthenticator } from "@aws-amplify/ui-react";

const HeaderNav = () => {
  const navigate = useNavigate();
  const { signOut, user } = useAuthenticator();
  return (
    <>
      {baseConfig.projectLink ? (
        <div className="github-link">
          <Link
            href={baseConfig.projectLink}
            isExternal={true}
            ariaLabel="github"
          >
            <AiFillGithub />
          </Link>
        </div>
      ) : (
        <></>
      )}
      <Menu
        menuAlign="end"
        trigger={
          <MenuButton variation="menu">          
            <div>
              {user.username} 
            </div>
          </MenuButton>
        }
      >
        <MenuItem onClick={signOut}>Logout</MenuItem>
      </Menu>
    </>
  );
};

export default HeaderNav;
