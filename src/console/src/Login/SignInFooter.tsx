import { Flex, Link, useAuthenticator, useTheme } from "@aws-amplify/ui-react";

export function SignInFooter() {
  const { toForgotPassword } = useAuthenticator();
  const { tokens } = useTheme();

  return (
    <Flex justifyContent="center" padding={`0 0 ${tokens.space.medium}`}>
      <Link onClick={toForgotPassword}>Reset your password</Link>
    </Flex>
  );
}