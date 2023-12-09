import React from "react";
import { Flex, Text, Button } from "@aws-amplify/ui-react";
import { useAuthenticator } from "@aws-amplify/ui-react";

const ProfileInformation = () => {
  const { signOut, user } = useAuthenticator();
  return (
    <div className="profile-card-content">
      <Text fontWeight="600" fontSize="18px" marginBottom="14px">
        Profile Information
      </Text>
      <Flex>
        <Text variation="tertiary" fontWeight="600">
          Full Name:
        </Text>
        <Text variation="tertiary">Clark Mathews</Text>
      </Flex>
      <Flex>
        <Text variation="tertiary" fontWeight="600">
          Phone:
        </Text>
        <Text variation="tertiary">(44) 123 1234 123</Text>
      </Flex>
      <Flex>
        <Text variation="tertiary" fontWeight="600">
          Email:
        </Text>
        <Text variation="tertiary">{user.username}</Text>
      </Flex>
      <Flex>
        <Text variation="tertiary" fontWeight="600">
          Location:
        </Text>
        <Text variation="tertiary">United States</Text>
      </Flex>
      <div className="profile-card-edit">
        <Button marginLeft="auto">Edit</Button>
      </div>
    </div>
  );
};

export default ProfileInformation;
