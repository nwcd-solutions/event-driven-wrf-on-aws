import {
    Authenticator,
    Flex,
    Grid,
    Image,
    Text,
    useTheme,
    View
  } from "@aws-amplify/ui-react";
  
  import { Header } from "./Header";
  import { Footer } from "./Footer";
  import { SignInHeader } from "./SignInHeader";
  import { SignInFooter } from "./SignInFooter";
  
  const components = {
    //Header,
    SignIn: {
      Header: SignInHeader,
      Footer: SignInFooter
    },
    Footer
  };
  
  export function Login() {
    const { tokens } = useTheme();
  
    return (
      <Grid templateColumns={{ base: "1fr 0", medium: "1fr 1fr" }}>
        <Flex

          justifyContent="center"
        >
          <Authenticator components={components}>
            {({ signOut, user }) => (
                <main>
                      <h1>Hello {user?.username}</h1>
                      <button onClick={signOut}>Sign out</button>
                </main>
            )}
          </Authenticator>
        </Flex>
        <View height="100vh">
          <Image
            alt="Amplify logo"
            src="/assets/wrf001.jpg"
            width="100%"
            height="100%"
            objectFit="cover"
          />
        </View>
      </Grid>
    );
  }
  
