import React, { useState,SyntheticEvent } from "react";
import {
  Button,
  Flex,
  Text,
  TextField,
} from "@aws-amplify/ui-react";
import { Parameter } from "./Parameter";

interface EditParameterProps {
  parameter: Parameter;
  onCancel: () => void;
  onSave: (parameter:Parameter) => void;
}

const EditParameter= ({ 
  parameter: initialValues,
  onCancel ,onSave 
}: EditParameterProps) => {
  const [parameter, setParameter] = useState(initialValues);

  const handleChange = (e: { target: { name: any; value: any; }; }) => {
    const { name, value } = e.target;
    setParameter({
      ...parameter,
      [name]: value,
    });
  };

  const handleSubmit = (event: SyntheticEvent) => {
    event.preventDefault();
    onSave(parameter);
};

  return (
    <>
      <Flex as="form" direction="column" width="100%" onSubmit={handleSubmit}>
        <TextField
          value={parameter.name}
          name="name"
          isDisabled={true}
          label={
            <Text>
              Parameter Name
              <Text as="span" fontSize="0.8rem" color="red" />
            </Text>
          }
          type="text"
        />
        <TextField
          value={parameter.description}
          isDisabled={true}
          name="Description"
          label={
            <Text>
              Description
              <Text as="span" fontSize="0.8rem" color="red" />
            </Text>
          }
          type="text"
        />
        <TextField
          defaultValue={parameter.value}
          onChange={handleChange}
          name="value"
          label={
            <Text>
              Value to be updated            
            </Text>
          }
          type="text"
        />
        <Flex>       
        <Button
          width={{ base: "100%", large: "50%" }}
          style={{ marginLeft: "auto" }}
          onClick={onCancel}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variation="primary"
          width={{ base: "100%", large: "50%" }}
          style={{ marginLeft: "auto" }}
          onSubmit={handleSubmit}
        >
          Submit
        </Button>
        </Flex>
      </Flex>
        
    </>
  );
};

export default EditParameter;
