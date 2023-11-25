### Getting Started - Creating the React Application

To get started, we first need to create a new React project & change into the new directory using the [Create React App CLI](https://github.com/facebook/create-react-app).

If you already have this installed, skip to the next step. If not, either install the CLI & create the app or create a new app using npx:

```bash
npm install -g create-react-app
create-react-app my-amplify-app --template typescript
```

Or use npx (npm 5.2 & later) to create a new app:

```bash
npx create-react-app my-amplify-app
```

Now change into the new app directory & install the AWS Amplify & AWS Amplify React libraries:

```bash
cd my-amplify-app
npm install --save aws-amplify @aws-amplify/ui-react uuid
# or
yarn add aws-amplify aws-amplify-react uuid
```
### Configuring the React applicaion

Create backend resources & set the parameters in __src/aws-exports.js__(if use Amplify to create backend ,this file will be auto-generated)

To configure the app, open __src/App.tsx__ and add the following code below the last import:

```tsx
import { Amplify } from 'aws-amplify'
import config from './aws-exports'
Amplify.configure(config)
```

Now, our app is ready to start using our AWS services.

### Using the withAuthenticator component

To add authentication, first import the `AmplifyProvider` and `Authenticator` HOC (Higher Order Component) from `@aws-amplify/ui-react`:

### src/App.js

```tsx
import {
  AmplifyProvider,
  Authenticator
} from '@aws-amplify/ui-react'
```



```sh
# run the app

npm start
```

Now, we can run the app and see that an Authentication flow has been added in front of our App component. This flow gives users the ability to sign up & sign in.

> To view the new user that was created in Cognito, go back to the dashboard at [https://console.aws.amazon.com/cognito/](https://console.aws.amazon.com/cognito/). Also be sure that your region is set correctly.

### Accessing User Data

We can access the user's info now that they are signed in by calling `Auth.currentAuthenticatedUser()`.

### src/App.js

```js
import React, { useEffect } from 'react'
import { Auth } from 'aws-amplify'

function App() {
  useEffect(() => {
    Auth.currentAuthenticatedUser()
      .then(user => console.log({ user }))
      .catch(error => console.log({ error }))
  })
  return (
    <div className="App">
      <p>
        Edit <code>src/App.js</code> and save to reload.
      </p>
    </div>
  )
}

export default App
```

### Custom authentication strategies

The `withAuthenticator` component is a really easy way to get up and running with authentication, but in a real-world application we probably want more control over how our form looks & functions.

Let's look at how we might create our own authentication flow.

To get started, we would probably want to create input fields that would hold user input data in the state. For instance when signing up a new user, we would probably need 4 user inputs to capture the user's username, email, password, & phone number.

To do this, we could create some initial state for these values & create an event handler that we could attach to the form inputs:

```js
// initial state
import React, { useReducer } from 'react'

// define initial state
const initialState = {
  username: '', password: '', email: ''
}

// create reducer
function reducer(state, action) {
  switch(action.type) {
    case 'SET_INPUT':
      return { ...state, [action.inputName]: action.inputValue }
    default:
      return state
  }
}

// useReducer hook creates local state
const [state, dispatch] = useReducer(reducer, initialState)

// event handler
function onChange(e) {
  dispatch({
    type: 'SET_INPUT',
    inputName: e.target.name,
    inputValue: e.target.value
  })
}

// example of usage with input
<input
  name='username'
  placeholder='username'
  value={state.username}
  onChange={onChange}
/>
```
