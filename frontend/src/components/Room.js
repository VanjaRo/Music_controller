import React, { Component } from "react";
import { Grid, Typography, Button } from "@material-ui/core";
import CreateRoomPage from "./CreateRoomPage";

export default class Room extends Component {
  constructor(props) {
    super(props);
    this.state = {
      votesToSkip: 2,
      guestCanPause: true,
      isHost: false,
      showSettings: false,
    };

    this.roomCode = this.props.match.params.roomCode;
    this.leaveButtonPressed = this.leaveButtonPressed.bind(this);
    this.updateShowSettings = this.updateShowSettings.bind(this);
    this.renderSettings = this.renderSettings.bind(this);
    this.renderSettingsButton = this.renderSettingsButton.bind(this);
    this.getRoomDetails();
  }

  getRoomDetails() {
    fetch("/api/get-room" + "?code=" + this.roomCode)
      .then((response) => {
        if (!response.ok) {
          this.props.leaveRoomCallback();
          this.props.history.push("/");
        }
        return response.json();
      })
      .then((data) => {
        this.setState({
          votesToSkip: data.votes_to_skip,
          guestCanPause: data.guest_can_pause,
          isHost: data.is_host,
        });
      });
  }

  leaveButtonPressed() {
    const requestOptions = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    };
    fetch("/api/leave-room", requestOptions).then((response) => {
      this.props.leaveRoomCallback();
      this.props.history.push("/");
    });
  }

  updateShowSettings(value) {
    this.setState({
      showSettings: value,
    });
  }

  renderSettings() {
    return (
      <Grid container spacing={1} align="center">
        <Grid item xs={12}>
          <CreateRoomPage
            update={true}
            votesToSkip={this.state.votesToSkip}
            guestCanPause={this.state.guestCanPause}
            roomCode={this.state.roomCode}
            updateCallback={() => {}}
          ></CreateRoomPage>
        </Grid>
        <Grid item xs={12}>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => this.updateShowSettings(false)}
          >
            Close
          </Button>
        </Grid>
      </Grid>
    );
  }

  renderSettingsButton() {
    return (
      <Grid item xs={12}>
        <Button
          variant="contained"
          color="primary"
          onClick={() => this.updateShowSettings(true)}
        >
          Settings
        </Button>
      </Grid>
    );
  }

  render() {
    if (this.state.showSettings) {
      return this.renderSettings();
    }
    return (
      <div>
        <Grid container spacing={1} align="center">
          <Grid item xs={12}>
            <Typography variant="h4" component="h4">
              Party Code: {this.roomCode}
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <Typography variant="h6" component="h4">
              Votes To Skip: {this.state.votesToSkip}
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <Typography variant="h6" component="h4">
              Guest Can Pause: {this.state.guestCanPause.toString()}
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <Typography variant="h6" component="h4">
              Is Host: {this.state.isHost.toString()}
            </Typography>
          </Grid>
          {this.state.isHost ? this.renderSettingsButton() : null}
          <Grid item xs={12}>
            <Button
              variant="text"
              color="secondary"
              onClick={this.leaveButtonPressed}
            >
              Leave Room
            </Button>
          </Grid>
        </Grid>
      </div>
    );
  }
}

{
  /* <h3>{this.roomCode}</h3>
        <p>Votes To Skip: {this.state.votesToSkip}</p>
        <p>Guest Can Pause: {this.state.guestCanPause.toString()}</p>
        <p>Is Host: {this.state.isHost.toString()}</p> */
}
