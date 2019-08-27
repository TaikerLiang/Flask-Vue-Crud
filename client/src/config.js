let config;

console.log(process.env);

if (process.env.VUE_APP_ENV === "dev") {
  config = {
    $api_url: "http://localhost",
    timeoutDuration: 30000,
    devServer: {
        disableHostCheck: true
    }
  };
} else {
  config = {
    $api_url: "https://api.taiker.space",
    timeoutDuration: 1000,
    devServer: {
        disableHostCheck: true
    }
  };
}

export { config }
