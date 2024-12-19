import React, { useState, useEffect, createContext, useContext, useCallback, useRef } from 'react';
import { useUser } from './UserContext.js';
import { useNavigate } from 'react-router-dom';
import api from '../services/api.js';


const WebSocketContext = createContext(null);

const getWindowURLinfo = () => {
  const host = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';

  return { host, port, protocol };
};

export const WebSocketProvider = ({ children }) => {
  const [friends, setFriends] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [socket, setSocket] = useState(null);
  const { user, isAuthenticated, logout, updateUser, checkFriends } = useUser();
  const socketRef = useRef(null);
  const navigate = useNavigate();

  const createWebSocketConnection = useCallback(async () => {
    if (!isAuthenticated || socketRef.current) {
      return;
    }

    try {
      // Get access_token from back-end
      const response = await api.get('/authentication/auth/token/get-access/');
      const wsToken = response.data.token;
      const { host, port, protocol } = getWindowURLinfo();

      const newSocket = new WebSocket(`${protocol}://${host}:8080/ws/authentication/?token=${wsToken}/`);
      newSocket.onopen = () => {
        console.log('WebSocket connected');
        setSocket(newSocket);
        socketRef.current = newSocket;
      };

      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('data: ', data);

        switch (data.type) {
          case 'friend_list_user_update':
            console.log('friend_list_user_update', data.user);
            if (user && user.friends) {
              const updatedFriends = user.friends.map(friend => 
                friend.id === data.id ? {
                  ...friend, username: data.username, status: data.status
                } : friend
              );

              updateUser({ friends: updatedFriends });
            }
            checkFriends();
            break;
          case 'notification':
            console.log('notification_type = ', data.notification_type);
            //setNotifications(prev => [...prev, data.notification]);
            setNotifications(prevNotifs => {
              const newNotifs = [...prevNotifs];
              // Vérifier si la notification n'existe pas déjà
              if (!newNotifs.some(n => n.id === data.id)) {
                newNotifs.push(data);
              }
              return newNotifs;
            });
            break;
          case 'friend_status':
            console.log('friend_status = ', data.status);
            console.log('friend = ', data.friend);
            break;
          case 'disconnected_from_server':
            try {
              logout();
              navigate('/forced-logout');
            } catch (err) {
              console.log('Failed Required Disconnect from the server from this browser');
            }
            break;
          default:
            console.log('Unknown message type: ', data.type);
        }
      };

      newSocket.onclose = () => {
        console.log('WebSocket disconnected');
        setSocket(null);
        socketRef.current = null;
      }

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated && !socketRef.current) {
      createWebSocketConnection();
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [isAuthenticated, createWebSocketConnection]);
  
  const value = React.useMemo(() => ({
    socket,
    friends,
    notifications,
    setNotifications
  }), [socket, friends, notifications]);

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
